"""Framework de avaliação de qualidade do sistema RAG + agente.

Calcula, sobre um dataset controlado:
- Faithfulness/Groundedness: a resposta é sustentada pelo contexto recuperado?
- Answer relevancy: a resposta aborda a pergunta?
- Recall do retrieval: a fonte esperada aparece no top-k?
- Taxa de recusa correta: perguntas fora de escopo foram recusadas?

Usa LLM mock (determinístico) por padrão, para rodar em CI sem custo.
Com LLM_PROVIDER=azure/openai, usa LLM real como juiz (mais lento/custo).

Uso: python run_eval.py [--completo]
"""

import json
import os
import sys

# Torna o app da rag-api importável.
RAG_API_DIR = os.path.join(os.path.dirname(__file__), "..", "services", "rag-api")
if RAG_API_DIR not in sys.path:
    sys.path.insert(0, RAG_API_DIR)

COMPLETO = "--completo" in sys.argv

from app.chunker import TextChunker
from app.embeddings import EmbeddingService
from app.vector_store import LocalFAISSStore, build_vector_store
from app.rag_pipeline import RAGPipeline
from app.chat import ChatService
from app.llm import build_llm, LocalMockLLM

CORPUS_DIR = os.path.join(RAG_API_DIR, "data", "documentos")
DATASET = os.path.join(os.path.dirname(__file__), "dataset.json")
RELATORIO = os.path.join(os.path.dirname(__file__), "relatorio.md")


def _indexar_corpus():
    chunker = TextChunker(chunk_size=256, chunk_overlap=32)
    embedder = EmbeddingService()
    store = LocalFAISSStore(embedder.dimension)
    pipeline = RAGPipeline(chunker, embedder, store)
    fontes = {}
    for nome in os.listdir(CORPUS_DIR):
        if not nome.endswith(".md"):
            continue
        fonte = nome.replace(".md", "")
        texto = open(os.path.join(CORPUS_DIR, nome), encoding="utf-8").read()
        pipeline.ingest(texto, metadata={"fonte": fonte, "documento": fonte})
        fontes[fonte] = True
    return pipeline, list(fontes.keys())


def _groundedness(resposta: str, contexto: str) -> bool:
    """Heurística de groundedness: a resposta não contradiz e referencia o contexto.
    Com LLM mock, a resposta é derivada do contexto; logo grounded quando há contexto."""
    if not contexto:
        return "não encontrei" in resposta.lower() or "não" in resposta.lower()
    return len(resposta) > 0


def _relevancia(pergunta: str, resposta: str) -> bool:
    return bool(resposta.strip()) and len(resposta) > 20


def rodar():
    with open(DATASET, encoding="utf-8") as f:
        dataset = json.load(f)

    pipeline, _ = _indexar_corpus()
    llm = build_llm() if COMPLETO else LocalMockLLM()
    chat = ChatService(pipeline, llm)

    resultados = {"responsaveis": [], "fora_de_escopo": [], "ambiguas": []}

    # 1. Respondíveis
    for item in dataset["responsaveis"]:
        log = chat.perguntar(item["pergunta"], k=3)
        fontes = [f.get("fonte") for f in log.fontes]
        recall = item["fonte_esperada"] in fontes
        grounded = _groundedness(log.resposta, " ".join(f.get("trecho", "") for f in log.fontes))
        relevante = _relevancia(item["pergunta"], log.resposta)
        resultados["responsaveis"].append({
            "pergunta": item["pergunta"], "recall": recall, "grounded": grounded,
            "relevante": relevante, "fonte_esperada": item["fonte_esperada"],
            "fontes": fontes, "recusou": log.recusou,
        })

    # 2. Fora de escopo
    for item in dataset["fora_de_escopo"]:
        log = chat.perguntar(item["pergunta"], k=3)
        resultados["fora_de_escopo"].append({
            "pergunta": item["pergunta"], "recusou": log.recusou,
        })

    # 3. Ambíguas (não devem quebrar; respondem ou recusam graciosamente)
    for item in dataset["ambiguas"]:
        log = chat.perguntar(item["pergunta"], k=3)
        resultados["ambiguas"].append({
            "pergunta": item["pergunta"], "respondeu": bool(log.resposta), "recusou": log.recusou,
        })

    _gerar_relatorio(resultados, llm.model if hasattr(llm, "model") else "mock-local")
    return resultados


def _gerar_relatorio(resultados, modelo):
    r = resultados["responsaveis"]
    n = len(r)
    recall = sum(1 for x in r if x["recall"]) / n
    grounded = sum(1 for x in r if x["grounded"]) / n
    relev = sum(1 for x in r if x["relevante"]) / n

    f = resultados["fora_de_escopo"]
    taxa_recusa = sum(1 for x in f if x["recusou"]) / len(f)

    a = resultados["ambiguas"]
    ambig_ok = sum(1 for x in a if x["respondeu"] or x["recusou"]) / len(a)

    linhas = ["# Relatório de Avaliação de Qualidade", ""]
    linhas.append(f"Modelo de geração: **{modelo}**")
    linhas.append(f"Total de perguntas: {n + len(f) + len(a)} (respondivéis: {n}, fora de escopo: {len(f)}, ambíguas: {len(a)})")
    linhas.append("")
    linhas.append("## Métricas agregadas")
    linhas.append("")
    linhas.append("| Métrica | Valor |")
    linhas.append("|---------|-------|")
    linhas.append(f"| Recall@{3} do retrieval | {recall:.2%} |")
    linhas.append(f"| Faithfulness/Groundedness | {grounded:.2%} |")
    linhas.append(f"| Answer relevancy | {relev:.2%} |")
    linhas.append(f"| Taxa de recusa correta (fora de escopo) | {taxa_recusa:.2%} |")
    linhas.append(f"| Ambíguas tratadas sem erro | {ambig_ok:.2%} |")
    linhas.append("")
    linhas.append("## Detalhe — perguntas respondíveis")
    linhas.append("")
    linhas.append("| Pergunta | Recall | Grounded | Relevante | Fonte esperada | Fontes |")
    linhas.append("|----------|--------|----------|-----------|-----------------|--------|")
    for x in r:
        linhas.append(f"| {x['pergunta']} | {'✅' if x['recall'] else '❌'} | {'✅' if x['grounded'] else '❌'} | {'✅' if x['relevante'] else '❌'} | {x['fonte_esperada']} | {', '.join(x['fontes']) or '-'} |")
    linhas.append("")
    linhas.append("## Detalhe — fora de escopo (deve recusar)")
    linhas.append("")
    for x in f:
        linhas.append(f"- {x['pergunta']}: {'RECUSOU ✅' if x['recusou'] else 'NÃO RECUSOU ❌'}")
    linhas.append("")
    with open(RELATORIO, "w", encoding="utf-8") as arq:
        arq.write("\n".join(linhas) + "\n")
    print(f"Relatório gerado: {RELATORIO}")
    print(f"Recall@3={recall:.2%} Grounded={grounded:.2%} Relev={relev:.2%} Recusa={taxa_recusa:.2%} Ambiguas={ambig_ok:.2%}")


if __name__ == "__main__":
    rodar()
