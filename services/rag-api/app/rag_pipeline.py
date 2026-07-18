from app.chunker import TextChunker
from app.embeddings import EmbeddingService
from app.vector_store import VectorStore


class RAGPipeline:
    def __init__(self, chunker: TextChunker, embedder: EmbeddingService, store: VectorStore):
        self.chunker = chunker
        self.embedder = embedder
        self.store = store

    def ingest(self, text: str, metadata: dict | None = None) -> list[str]:
        chunks = self.chunker.chunk(text)
        doc_ids = []
        for chunk in chunks:
            embedding = self.embedder.embed(chunk["text"])
            doc_id = self.store.add(
                text=chunk["text"],
                embedding=embedding,
                metadata=metadata,
            )
            doc_ids.append(doc_id)
        return doc_ids

    def query(self, question: str, k: int = 3) -> dict:
        query_embedding = self.embedder.embed(question)
        results = self.store.search(query_embedding, k=k)

        context = "\n\n".join(r["text"] for r in results)

        answer = self._generate(question, context)

        return {
            "question": question,
            "answer": answer,
            "sources": [
                {"text": r["text"], "score": r["score"]}
                for r in results
            ],
        }

    def _generate(self, question: str, context: str) -> str:
        if not context:
            return "Não encontrei informações relevantes para responder à sua pergunta."

        return (
            f"Com base nos documentos analisados, encontrei as seguintes informações "
            f"relacionadas à sua pergunta:\n\n{context}"
        )
