from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
import os

from app.chunker import TextChunker
from app.embeddings import EmbeddingService
from app.vector_store import build_vector_store
from app.rag_pipeline import RAGPipeline
from app.chat import ChatService
from app.agent import AgentExecutor, MockPlanner
from app.multiagent import MultiAgentOrchestrator, AttendanceAgent, ComplianceReviewer
from app.multimodal import build_extractor
from app.auth import exigir_admin, exigir_usuario, criar_token_teste

app = FastAPI(title="RAG API - Agente Previdência IA")

chunker = TextChunker()
embedder = EmbeddingService()
store = build_vector_store(embedder.dimension)
pipeline = RAGPipeline(chunker, embedder, store)
chat_service = ChatService(pipeline)
agent_executor = AgentExecutor(planner=MockPlanner())


def _gerador_atendimento(instrucao, tentativa, problemas):
    """Gera a resposta do Agente de Atendimento via RAG/chat. Nas tentativas seguintes,
    inclui automaticamente disclaimer e citação de fonte para satisfazer o Compliance."""
    log = chat_service.perguntar(instrucao)
    resposta = log.resposta
    fontes = [f.get("fonte") for f in log.fontes]
    if tentativa > 1:
        resposta = resposta + "\n\n(Fonte: documentos internos da seguradora. Esta é uma informação educativa e não constitui recomendação financeira individualizada.)"
        fontes = fontes or ["documentos internos"]
    return resposta, fontes


multi_orchestrator = MultiAgentOrchestrator(
    AttendanceAgent(_gerador_atendimento),
    ComplianceReviewer(),
    max_iteracoes=3,
)
extractor = build_extractor()


class IngestRequest(BaseModel):
    text: str
    metadata: dict | None = None


class QueryRequest(BaseModel):
    question: str
    k: int = 3


class IngestResponse(BaseModel):
    chunk_count: int
    doc_ids: list[str]


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[dict]


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/documents/ingest", response_model=IngestResponse)
async def ingest_document(req: IngestRequest):
    if not req.text.strip():
        raise HTTPException(400, "text cannot be empty")
    doc_ids = pipeline.ingest(req.text, req.metadata)
    return IngestResponse(chunk_count=len(doc_ids), doc_ids=doc_ids)


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(400, "question cannot be empty")
    if req.k < 1:
        raise HTTPException(400, "k must be >= 1")
    result = pipeline.query(req.question, k=req.k)
    return QueryResponse(**result)


class BuscarRequest(BaseModel):
    pergunta: str
    k: int = 3
    score_min: float = 0.0


class BuscarResponse(BaseModel):
    pergunta: str
    resultados: list[dict]


@app.post("/retrieval/buscar", response_model=BuscarResponse)
async def buscar(req: BuscarRequest):
    """Retrieval puro (sem geração): retorna os top-k chunks relevantes com score e fonte."""
    if not req.pergunta.strip():
        raise HTTPException(400, "pergunta cannot be empty")
    if req.k < 1:
        raise HTTPException(400, "k must be >= 1")
    resultados = pipeline.retrieve(req.pergunta, k=req.k)
    resultados = [r for r in resultados if r.get("score", 0) >= req.score_min]
    return BuscarResponse(pergunta=req.pergunta, resultados=resultados)


@app.get("/documents/count")
async def document_count():
    return {"total_chunks": store.count()}


class PerguntarRequest(BaseModel):
    pergunta: str
    k: int = 3
    historico: list | None = None


class PerguntarResponse(BaseModel):
    pergunta: str
    resposta: str
    fontes: list
    recusou: bool
    tokens_prompt: int
    tokens_completion: int
    latencia_ms: float
    custo_usd: float
    modelo: str


@app.post("/chat/perguntar", response_model=PerguntarResponse)
async def perguntar(req: PerguntarRequest):
    if not req.pergunta.strip():
        raise HTTPException(400, "pergunta cannot be empty")
    log = chat_service.perguntar(req.pergunta, k=req.k, historico=req.historico)
    return PerguntarResponse(
        pergunta=log.pergunta,
        resposta=log.resposta,
        fontes=log.fontes,
        recusou=log.recusou,
        tokens_prompt=log.tokens_prompt,
        tokens_completion=log.tokens_completion,
        latencia_ms=log.latencia_ms,
        custo_usd=log.custo_usd,
        modelo=log.modelo,
    )


class ExecutarRequest(BaseModel):
    instrucao: str


class ExecutarResponse(BaseModel):
    execucao_id: str
    resposta_final: str
    concluido: bool
    motivo_parada: str
    passos: list


@app.post("/agente/executar", response_model=ExecutarResponse)
async def agente_executar(req: ExecutarRequest):
    if not req.instrucao.strip():
        raise HTTPException(400, "instrucao cannot be empty")
    execucao = agent_executor.run(req.instrucao)
    return ExecutarResponse(
        execucao_id=execucao.id,
        resposta_final=execucao.resposta_final,
        concluido=execucao.concluido,
        motivo_parada=execucao.motivo_parada,
        passos=[p.__dict__ for p in execucao.passos],
    )


@app.get("/agente/execucoes/{exec_id}")
async def agente_execucao(exec_id: str):
    execucao = agent_executor.get_execution(exec_id)
    if execucao is None:
        raise HTTPException(404, "execução não encontrada")
    return execucao.__dict__


class MultiExecutarRequest(BaseModel):
    instrucao: str


@app.post("/multiagente/executar")
async def multiagente_executar(req: MultiExecutarRequest):
    if not req.instrucao.strip():
        raise HTTPException(400, "instrucao cannot be empty")
    trace = multi_orchestrator.executar(req.instrucao)
    return trace.__dict__


@app.get("/multiagente/traces/{trace_id}")
async def multiagente_trace(trace_id: str):
    trace = multi_orchestrator.get_trace(trace_id)
    if trace is None:
        raise HTTPException(404, "trace não encontrado")
    return trace.__dict__


@app.get("/metrics")
async def metrics(_usuario: dict = Depends(exigir_usuario)):
    """Dashboard simples: nº de chunks indexados, queries (log), latência/custo acumulados."""
    try:
        import json
        queries = 0
        latencia = 0.0
        custo = 0.0
        caminho = os.path.join("logs", "interacoes.jsonl")
        if os.path.exists(caminho):
            with open(caminho, encoding="utf-8") as f:
                for linha in f:
                    if linha.strip():
                        q = json.loads(linha)
                        queries += 1
                        latencia += q.get("latencia_ms", 0)
                        custo += q.get("custo_usd", 0)
        return {
            "chunks_indexados": store.count(),
            "queries": queries,
            "latencia_media_ms": round(latencia / queries, 2) if queries else 0,
            "custo_acumulado_usd": round(custo, 4),
        }
    except Exception:
        return {"chunks_indexados": store.count(), "queries": 0, "observacao": "sem log de interações"}


@app.post("/admin/reindex")
async def reindex(_admin: dict = Depends(exigir_admin)):
    """Apenas admin (RBAC Entra ID) pode re-indexar documentos."""
    if os.path.isdir("data/documentos"):
        for nome in os.listdir("data/documentos"):
            if nome.endswith(".md"):
                texto = open(os.path.join("data/documentos", nome), encoding="utf-8").read()
                pipeline.ingest(texto, metadata={"fonte": nome.replace(".md", ""), "documento": nome})
    return {"status": "reindexado", "chunks": store.count()}


@app.post("/multimodal/extrair")
async def multimodal_extrair(file: UploadFile = File(...)):
    """Recebe uma imagem (boleto/carteirinha/apólice) e extrai dados estruturados."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "arquivo deve ser uma imagem")
    os.makedirs("uploads_tmp", exist_ok=True)
    caminho = os.path.join("uploads_tmp", file.filename or "imagem.png")
    with open(caminho, "wb") as f:
        f.write(await file.read())
    try:
        resultado = extractor.extrair(caminho)
    except Exception as e:
        raise HTTPException(500, f"erro na extração: {e}")
    return {
        "sucesso": resultado.sucesso,
        "dados": resultado.dados,
        "texto_bruto": resultado.texto_bruto,
        "observacao": resultado.observacao,
    }
