"""Gera dataset sintético de pares (pergunta, chunk) para fine-tuning de embeddings.

Estratégia:
- Positivos: para cada chunk do corpus, gera perguntas plausíveis (template + variações).
- Negativos: para cada pergunta, escolhe chunks de outros documentos como irrelevantes.

Saída: finetuning/data/dataset.jsonl com {query, positive, negative}.
"""

import json
import os
import re

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "services", "rag-api", "data", "documentos")
OUT = os.path.join(os.path.dirname(__file__), "data", "dataset.jsonl")

TEMPLATES = [
    "O que diz o manual sobre {topico}?",
    "Como funciona {topico}?",
    "Qual a regra de {topico}?",
    "Explique {topico}.",
    "Me fale sobre {topico}.",
]

TOPICOS_POR_DOC = {
    "manual_vida": ["seguro de vida", "indenização por morte", "beneficiário", "morte acidental", "isencao de IR"],
    "manual_previdencia": ["previdência", "carência para resgate", "tabela regressiva de IR", "resgate parcial", "portabilidade"],
    "manual_prestamista": ["seguro prestamista", "quitação de dívida", "cobertura do prestamista", "invalidez permanente", "prêmio do prestamista"],
}


def _carregar_chunks():
    chunks = []
    for nome in os.listdir(CORPUS_DIR):
        if not nome.endswith(".md"):
            continue
        caminho = os.path.join(CORPUS_DIR, nome)
        texto = open(caminho, encoding="utf-8").read()
        # chunk por parágrafo
        for parag in texto.split("\n\n"):
            parag = parag.strip()
            if len(parag) > 30:
                chunks.append({"fonte": nome.replace(".md", ""), "texto": parag})
    return chunks


def gerar():
    chunks = _carregar_chunks()
    por_fonte = {}
    for c in chunks:
        por_fonte.setdefault(c["fonte"], []).append(c)

    registros = []
    for fonte, topicos in TOPICOS_POR_DOC.items():
        base = por_fonte.get(fonte, [])
        for topico in topicos:
            for template in TEMPLATES[:3]:
                pergunta = template.format(topico=topico)
                # positivo: chunk da mesma fonte que menciona o tópico (ou o primeiro)
                positivo = next((c for c in base if topico.split()[0] in c["texto"].lower()), base[0] if base else None)
                if not positivo:
                    continue
                # negativo: chunk de outra fonte
                outras = [c for c in chunks if c["fonte"] != fonte]
                negativo = outras[hash(pergunta) % len(outras)] if outras else None
                if not negativo:
                    continue
                registros.append({
                    "query": pergunta,
                    "positive": positivo["texto"],
                    "negative": negativo["texto"],
                    "fonte": fonte,
                })

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Gerados {len(registros)} pares em {OUT}")


if __name__ == "__main__":
    gerar()
