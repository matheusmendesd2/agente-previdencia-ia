import abc
import os
import uuid

import numpy as np


class VectorStore(abc.ABC):
    """Interface abstrata de vector store.

    Duas implementações estão disponíveis e selecionáveis por variável de ambiente
    (VECTOR_STORE): 'local' (FAISS, sem custo) e 'azure' (Azure AI Search).
    O default é 'local' para garantir execução 100% gratuita em dev/CI.
    """

    @abc.abstractmethod
    def add(self, text: str, embedding: np.ndarray, metadata: dict | None = None) -> str:
        ...

    @abc.abstractmethod
    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[dict]:
        ...

    @abc.abstractmethod
    def count(self) -> int:
        ...

    @abc.abstractmethod
    def clear(self) -> None:
        ...


class LocalFAISSStore(VectorStore):
    """Implementação local com FAISS (IndexFlatL2). Não requer credenciais."""

    def __init__(self, dimension: int):
        import faiss

        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.documents: list[dict] = []

    def add(self, text: str, embedding: np.ndarray, metadata: dict | None = None) -> str:
        doc_id = str(uuid.uuid4())
        embedding = embedding.astype(np.float32).reshape(1, -1)
        self.index.add(embedding)
        self.documents.append({"id": doc_id, "text": text, "metadata": metadata or {}})
        return doc_id

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[dict]:
        if self.index.ntotal == 0:
            return []
        k = min(k, self.index.ntotal)
        query_embedding = query_embedding.astype(np.float32).reshape(1, -1)
        distances, indices = self.index.search(query_embedding, k)
        results = []
        for i, idx in enumerate(indices[0]):
            results.append({**self.documents[idx], "score": float(distances[0][i])})
        return results

    def count(self) -> int:
        return self.index.ntotal

    def clear(self):
        import faiss

        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents.clear()


class AzureAISearchStore(VectorStore):
    """Implementação contra Azure AI Search.

    Requer credenciais (AZURE_AI_SEARCH_ENDPOINT, AZURE_AI_SEARCH_KEY, AZURE_AI_SEARCH_INDEX).
    Documentada e pronta para uso; em ambiente sem credenciais ela NÃO é instanciada
    (o sistema usa LocalFAISSStore por padrão). Veja README de rag-api.
    """

    def __init__(self, dimension: int):
        endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        key = os.getenv("AZURE_AI_SEARCH_KEY")
        index = os.getenv("AZURE_AI_SEARCH_INDEX", "rag-index")
        if not endpoint or not key:
            raise RuntimeError(
                "AZURE_AI_SEARCH_ENDPOINT e AZURE_AI_SEARCH_KEY são obrigatórios para usar AzureAISearchStore."
            )
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient
        from azure.search.documents.models import VectorizedQuery

        self.index = index
        self._client = SearchClient(endpoint=endpoint, index_name=index, credential=AzureKeyCredential(key))
        self._vectorized = VectorizedQuery
        self.dimension = dimension

    def add(self, text: str, embedding: np.ndarray, metadata: dict | None = None) -> str:
        doc_id = str(uuid.uuid4())
        self._client.upload_documents([{
            "id": doc_id,
            "content": text,
            "embedding": embedding.astype(np.float32).tolist(),
            "metadata": metadata or {},
        }])
        return doc_id

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[dict]:
        vq = self._vectorized(vector=query_embedding.astype(np.float32).tolist(), k=k, fields="embedding")
        results = self._client.search(vector_queries=[vq])
        return [{"id": r["id"], "text": r["content"], "metadata": r.get("metadata", {}), "score": float(r["@search.score"])} for r in results]

    def count(self) -> int:
        return sum(1 for _ in self._client.search("*"))

    def clear(self):
        # Azure AI Search não possui "clear" trivial; operação manual no portal.
        raise NotImplementedError("Limpeza do índice Azure deve ser feita no portal ou via script dedicado.")


def build_vector_store(dimension: int) -> VectorStore:
    """Factory que seleciona a implementação via VECTOR_STORE (default: local)."""
    kind = (os.getenv("VECTOR_STORE") or "local").lower()
    if kind == "azure":
        return AzureAISearchStore(dimension)
    return LocalFAISSStore(dimension)
