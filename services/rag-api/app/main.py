from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.chunker import TextChunker
from app.embeddings import EmbeddingService
from app.vector_store import VectorStore
from app.rag_pipeline import RAGPipeline

app = FastAPI(title="RAG API - Agente Previdência IA")

chunker = TextChunker()
embedder = EmbeddingService()
store = VectorStore(embedder.dimension)
pipeline = RAGPipeline(chunker, embedder, store)


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


@app.get("/documents/count")
async def document_count():
    return {"total_chunks": store.count()}
