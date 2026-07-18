from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.chunker import TextChunker
from app.embeddings import EmbeddingService
from app.vector_store import build_vector_store
from app.rag_pipeline import RAGPipeline
from app.chat import ChatService

app = FastAPI(title="RAG API - Agente Previdência IA")

chunker = TextChunker()
embedder = EmbeddingService()
store = build_vector_store(embedder.dimension)
pipeline = RAGPipeline(chunker, embedder, store)
chat_service = ChatService(pipeline)


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
