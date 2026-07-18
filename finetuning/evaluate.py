"""Compara retrieval do modelo base vs. modelo ajustado e gera relatório.

Uso:
    python evaluate.py            # avalia base e ajustado (se existir) e gera RESULTADOS.md
    python evaluate.py --base-only
"""

import os
import sys

import finetune as ft

RESULTADOS = os.path.join(os.path.dirname(__file__), "RESULTADOS.md")
MODELO_AJUSTADO = os.path.join(os.path.dirname(__file__), "modelo_ajustado")
MODELO_BASE_TEMP = os.path.join(os.path.dirname(__file__), "modelo_base_temp")


def _garantir_base_temp():
    if not os.path.exists(MODELO_BASE_TEMP):
        from sentence_transformers import SentenceTransformer
        SentenceTransformer(ft.MODELO_BASE).save(MODELO_BASE_TEMP)
    return MODELO_BASE_TEMP


def main():
    base_path = _garantir_base_temp()
    print("Avaliando modelo BASE...")
    base_metrics = ft.avaliar(base_path)

    resultado = {
        "base": base_metrics,
        "ajustado": None,
    }

    if "--base-only" not in sys.argv and os.path.exists(MODELO_AJUSTADO):
        print("Avaliando modelo AJUSTADO...")
        resultado["ajustado"] = ft.avaliar(MODELO_AJUSTADO)

    _escrever_relatorio(resultado)
    print(f"Relatório em {RESULTADOS}")


def _escrever_relatorio(m):
    linhas = ["# Resultados de Fine-tuning de Embeddings", ""]
    linhas.append(f"Dataset: {m['base']['n']} pares sintéticos (gerados de `services/rag-api/data/documentos`).")
    linhas.append("")
    linhas.append("| Métrica | Modelo Base | Modelo Ajustado |")
    linhas.append("|---------|------------|----------------|")
    if m["ajustado"]:
        linhas.append(f"| Recall@{m['base']['k']} | {m['base']['recall@k']:.3f} | {m['ajustado']['recall@k']:.3f} |")
        linhas.append(f"| MRR | {m['base']['mrr']:.3f} | {m['ajustado']['mrr']:.3f} |")
    else:
        linhas.append(f"| Recall@{m['base']['k']} | {m['base']['recall@k']:.3f} | (modelo ajustado não treinado ainda) |")
        linhas.append(f"| MRR | {m['base']['mrr']:.3f} | - |")
    linhas.append("")
    linhas.append("## Observações")
    linhas.append("- Modelo base: `all-MiniLM-L6-v2`. Modelo ajustado: mesmo modelo com contrastive learning (MultipleNegativesRankingLoss).")
    linhas.append("- Mesmo com dataset pequeno/sintético, o processo é 100% reproduzível via `python run_all.py`.")
    linhas.append("- Para treinar: `python finetune.py`; para avaliar: `python evaluate.py`.")
    with open(RESULTADOS, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas) + "\n")


if __name__ == "__main__":
    main()
