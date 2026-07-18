import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)

    def embed(self, text: str) -> np.ndarray:
        self._load_model()
        return self._model.encode(text)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        self._load_model()
        return self._model.encode(texts)

    @property
    def dimension(self) -> int:
        self._load_model()
        return self._model.get_embedding_dimension()
