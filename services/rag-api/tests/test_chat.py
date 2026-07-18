from app.chunker import TextChunker
from app.embeddings import EmbeddingService
from app.vector_store import LocalFAISSStore
from app.rag_pipeline import RAGPipeline
from app.chat import ChatService
from app.llm import LocalMockLLM


def _pipeline_indexado():
    chunker = TextChunker(chunk_size=256, chunk_overlap=32)
    embedder = EmbeddingService()
    store = LocalFAISSStore(embedder.dimension)
    pipeline = RAGPipeline(chunker, embedder, store)
    pipeline.ingest(
        "O plano de previdência possui carência de 6 meses para resgate. O IR segue tabela regressiva.",
        metadata={"fonte": "manual_previdencia"},
    )
    pipeline.ingest(
        "O seguro de vida garante indenização por morte natural ou acidental ao beneficiário.",
        metadata={"fonte": "manual_vida"},
    )
    return pipeline


def test_pergunta_respondivel_cita_fonte():
    pipeline = _pipeline_indexado()
    svc = ChatService(pipeline, LocalMockLLM())
    log = svc.perguntar("Qual é a carência para resgate na previdência?")
    assert log.recusou is False
    assert log.resposta
    fontes = [f["fonte"] for f in log.fontes]
    assert "manual_previdencia" in fontes


def test_pergunta_fora_do_escopo_recusa():
    # Store vazio: nada recuperado -> sistema recusa em vez de alucinar.
    chunker = TextChunker()
    embedder = EmbeddingService()
    store = LocalFAISSStore(embedder.dimension)
    pipeline = RAGPipeline(chunker, embedder, store)
    svc = ChatService(pipeline, LocalMockLLM())
    log = svc.perguntar("Qual a receita do bolo de fubá?")
    assert log.recusou is True
    assert "não" in log.resposta.lower() or "não encontrei" in log.resposta.lower()


def test_log_custo_latencia_registrado():
    pipeline = _pipeline_indexado()
    svc = ChatService(pipeline, LocalMockLLM())
    log = svc.perguntar("O seguro de vida cobre morte acidental?")
    assert log.latencia_ms >= 0
    assert log.custo_usd == 0.0  # mock é gratuito
    assert log.modelo == "mock-local"
    assert log.tokens_prompt > 0
