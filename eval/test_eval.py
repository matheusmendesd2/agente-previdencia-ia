import os
import sys

HERE = os.path.dirname(__file__)
RAG_API_DIR = os.path.join(HERE, "..", "services", "rag-api")
if RAG_API_DIR not in sys.path:
    sys.path.insert(0, RAG_API_DIR)

import run_eval as ev


def test_run_eval_gera_relatorio_com_metricas():
    resultados = ev.rodar()
    relatorio = os.path.join(HERE, "relatorio.md")
    assert os.path.exists(relatorio)
    texto = open(relatorio, encoding="utf-8").read()
    # Métricas não podem ser vazias/None.
    assert "Recall@3" in texto
    assert "Taxa de recusa" in texto
    # Pelo menos uma pergunta respondível com recall e uma fora de escopo recusada.
    assert len(resultados["responsaveis"]) >= 10
    assert len(resultados["fora_de_escopo"]) >= 3
    assert any(x["recall"] for x in resultados["responsaveis"])
    assert any(x["recusou"] for x in resultados["fora_de_escopo"])
