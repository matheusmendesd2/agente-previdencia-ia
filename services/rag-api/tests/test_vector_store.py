import numpy as np
from app.vector_store import VectorStore


def test_add_and_count():
    store = VectorStore(dimension=4)
    emb = np.array([0.1, 0.2, 0.3, 0.4])
    store.add("texto exemplo", emb)
    assert store.count() == 1


def test_search_returns_results():
    store = VectorStore(dimension=2)
    store.add("gato", np.array([0.1, 0.2]))
    store.add("cachorro", np.array([0.9, 0.8]))
    results = store.search(np.array([0.1, 0.2]), k=2)
    assert len(results) == 2
    assert results[0]["text"] == "gato"


def test_search_empty():
    store = VectorStore(dimension=4)
    results = store.search(np.array([0.1, 0.2, 0.3, 0.4]))
    assert results == []


def test_clear():
    store = VectorStore(dimension=2)
    store.add("a", np.array([0.1, 0.2]))
    store.clear()
    assert store.count() == 0


def test_add_with_metadata():
    store = VectorStore(dimension=2)
    doc_id = store.add("test", np.array([0.1, 0.2]), {"source": "manual"})
    assert doc_id is not None
    assert len(doc_id) > 0
