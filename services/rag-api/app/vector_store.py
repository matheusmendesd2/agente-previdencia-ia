import uuid
import numpy as np
import faiss


class VectorStore:
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents: list[dict] = []

    def add(self, text: str, embedding: np.ndarray, metadata: dict | None = None) -> str:
        doc_id = str(uuid.uuid4())
        embedding = embedding.astype(np.float32).reshape(1, -1)
        self.index.add(embedding)
        self.documents.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {},
        })
        return doc_id

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[dict]:
        if self.index.ntotal == 0:
            return []
        k = min(k, self.index.ntotal)
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        distances, indices = self.index.search(query_embedding, k)
        results = []
        for i, idx in enumerate(indices[0]):
            results.append({
                **self.documents[idx],
                "score": float(distances[0][i]),
            })
        return results

    def count(self) -> int:
        return self.index.ntotal

    def clear(self):
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents.clear()
