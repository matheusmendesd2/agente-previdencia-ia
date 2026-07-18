import json
import os
import sys

import finetune as ft

RAG_API_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "services", "rag-api")
if RAG_API_DIR not in sys.path:
    sys.path.insert(0, RAG_API_DIR)

HERE = os.path.dirname(__file__)


def test_generate_dataset_formato(tmp_path):
    # Redireciona saída para tmp e gera.
    ft.DATASET = str(tmp_path / "dataset.jsonl")
    import generate_dataset
    generate_dataset.OUT = ft.DATASET
    generate_dataset.gerar()
    linhas = [json.loads(l) for l in open(ft.DATASET, encoding="utf-8") if l.strip()]
    assert len(linhas) > 0
    for r in linhas:
        assert set(["query", "positive", "negative"]).issubset(r.keys())
        assert isinstance(r["query"], str) and r["query"]


def test_finetune_carrega_e_dimensao(tmp_path):
    # Dataset mínimo em tmp para treino rápido.
    ds = str(tmp_path / "dataset.jsonl")
    with open(ds, "w", encoding="utf-8") as f:
        for i in range(4):
            f.write(json.dumps({
                "query": f"pergunta exemplo {i}",
                "positive": f"chunk relevante sobre seguro {i}",
                "negative": f"texto irrelevante sobre astrologia {i}",
            }) + "\n")
    ft.DATASET = ds
    saida = str(tmp_path / "modelo")
    ft.finetunar(epochs=1, saida=saida)

    from sentence_transformers import SentenceTransformer
    modelo = SentenceTransformer(saida)
    emb = modelo.encode(["teste"])
    assert emb.shape[1] == 384  # all-MiniLM-L6-v2


def test_avaliacao_roda_fim_a_fim(tmp_path):
    ds = str(tmp_path / "dataset.jsonl")
    with open(ds, "w", encoding="utf-8") as f:
        for i in range(6):
            f.write(json.dumps({
                "query": f"pergunta {i}",
                "positive": f"chunk relevante seguro {i}",
                "negative": f"irrelevante {i}",
            }) + "\n")
    ft.DATASET = ds
    base = str(tmp_path / "base_temp")
    from sentence_transformers import SentenceTransformer
    SentenceTransformer(ft.MODELO_BASE).save(base)
    metrics = ft.avaliar(base, k=2)
    assert "recall@k" in metrics and "mrr" in metrics
    assert 0.0 <= metrics["recall@k"] <= 1.0
    assert metrics["n"] == 6
