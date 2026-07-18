# finetuning (Tuning de embeddings)

Pipeline de fine-tuning do modelo de embeddings para o domínio de previdência,
com avaliação antes/depois usando Recall@3. Roda localmente com
`sentence-transformers` (sem custo).

## Rodar tudo

```bash
python run_all.py       # gera dataset, treina e avalia -> RESULTADOS.md
```

Ou por etapa: `generate_dataset.py` -> `finetune.py` -> `evaluate.py`.
Testes: `pytest tests/` (3 testes).

## Saídas

- `data/` — dataset sintético de pares pergunta/documento (gerado).
- `modelo_ajustado/` — modelo fine-tuned (artefato local, não versionado).
- `RESULTADOS.md` — comparação de métricas base vs. ajustado (Recall@3).

> Artefatos de modelo e dataset são ignorados no git por serem grandes/gerados.
