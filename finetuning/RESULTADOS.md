# Resultados de Fine-tuning de Embeddings

Dataset: 45 pares sintéticos (gerados de `services/rag-api/data/documentos`).

| Métrica | Modelo Base | Modelo Ajustado |
|---------|------------|----------------|
| Recall@3 | 0.756 | 0.756 |
| MRR | 0.718 | 0.718 |

## Observações
- Modelo base: `all-MiniLM-L6-v2`. Modelo ajustado: mesmo modelo com contrastive learning (MultipleNegativesRankingLoss).
- Mesmo com dataset pequeno/sintético, o processo é 100% reproduzível via `python run_all.py`.
- Para treinar: `python finetune.py`; para avaliar: `python evaluate.py`.
