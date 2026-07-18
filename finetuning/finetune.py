"""Fine-tuning leve de um modelo de embeddings open-source (contrastive learning).

Usa sentence-transformers com MultipleNegativesRankingLoss sobre o dataset sintético.
O modelo base é all-MiniLM-L6-v2 (pequeno). O modelo ajustado é salvo em finetuning/modelo_ajustado.
"""

import json
import os
import sys

import numpy as np

DATASET = os.path.join(os.path.dirname(__file__), "data", "dataset.jsonl")
MODELO_BASE = "all-MiniLM-L6-v2"
MODELO_SAIDA = os.path.join(os.path.dirname(__file__), "modelo_ajustado")

# Garante que o app da rag-api esteja importável (reutiliza chunker/store).
RAG_API_DIR = os.path.join(os.path.dirname(__file__), "..", "services", "rag-api")
if RAG_API_DIR not in sys.path:
    sys.path.insert(0, RAG_API_DIR)


def carregar_dataset():
    with open(DATASET, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def _embedder(modelo):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(modelo)


def finetunar(epochs: int = 1, saida: str = MODELO_SAIDA):
    from sentence_transformers import SentenceTransformer, InputExample, losses

    pares = carregar_dataset()
    treino = [InputExample(texts=[p["query"], p["positive"]]) for p in pares]
    modelo = SentenceTransformer(MODELO_BASE)
    perda = losses.MultipleNegativesRankingLoss(modelo)
    from torch.utils.data import DataLoader
    loader = DataLoader(treino, shuffle=True, batch_size=8, collate_fn=modelo.smart_batching_collate)
    modelo.fit([(loader, perda)], epochs=epochs, show_progress_bar=False)
    os.makedirs(saida, exist_ok=True)
    modelo.save(saida)
    print(f"Modelo ajustado salvo em {saida}")
    return saida


def avaliar(modelo_path: str, k: int = 3) -> dict:
    """Calcula Recall@{k} e MRR no dataset (query -> positive deve estar no top-k do corpus)."""
    from app.rag_pipeline import RAGPipeline  # reutiliza chunker/store locais
    from app.chunker import TextChunker
    from app.vector_store import LocalFAISSStore
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity

    pares = carregar_dataset()
    # Corpus = todos os positivos+negativos como documentos candidatos.
    corpus = []
    for p in pares:
        if p["positive"] not in corpus:
            corpus.append(p["positive"])
        if p["negative"] not in corpus:
            corpus.append(p["negative"])

    modelo = SentenceTransformer(modelo_path)
    corpus_emb = modelo.encode(corpus)
    queries = [p["query"] for p in pares]
    q_emb = modelo.encode(queries)

    recall = 0
    mrr = 0.0
    for i, p in enumerate(pares):
        sims = cosine_similarity([q_emb[i]], corpus_emb)[0]
        ordem = np.argsort(-sims)
        rank = np.where(ordem == corpus.index(p["positive"]))[0][0] + 1
        if rank <= k:
            recall += 1
        mrr += 1.0 / rank
    n = len(pares)
    return {"recall@k": recall / n, "mrr": mrr / n, "n": n, "k": k}


if __name__ == "__main__":
    import sys
    if "--eval-base" in sys.argv:
        base = _embedder(MODELO_BASE)
        # salva temporário para reuso
        tmp = os.path.join(os.path.dirname(__file__), "modelo_base_temp")
        base.save(tmp)
        print("BASE", avaliar(tmp))
    else:
        out = finetunar()
        print("AJUSTADO", avaliar(out))
