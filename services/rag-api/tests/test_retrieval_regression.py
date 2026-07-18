"""Teste de regressão de qualidade do retrieval.

Usa um corpus pequeno e controlado com perguntas cujo documento fonte esperado é conhecido.
Valida que o chunk correto aparece no top-3 (recall) e que a fonte é citada.
Não depende de credencial Azure (usa LocalFAISSStore).
"""

from app.chunker import TextChunker
from app.embeddings import EmbeddingService
from app.vector_store import LocalFAISSStore
from app.rag_pipeline import RAGPipeline

CORPUS = {
    "manual_vida": (
        "O seguro de vida garante uma indenização por morte natural ou acidental ao beneficiário "
        "indicado. A cobertura de morte acidental dobra o valor contratado. O pagamento é isento de IR."
    ),
    "manual_previdencia": (
        "O plano de previdência possui carência de 6 meses para resgate. O IR segue tabela regressiva: "
        "35% nos primeiros 12 meses, caindo para 10% após 60 meses. O resgate parcial é permitido."
    ),
    "manual_prestamista": (
        "O seguro prestamista quita a dívida do cliente em caso de morte ou invalidez permanente, "
        "protegendo o titular do crédito e sua família. A cobertura é limitada ao saldo devedor."
    ),
}

PERGUNTAS_ESPERADAS = [
    ("Qual é a carência para resgate na previdência?", "manual_previdencia"),
    ("O seguro de vida cobre morte acidental?", "manual_vida"),
    ("O que faz o seguro prestamista?", "manual_prestamista"),
    ("Como funciona o IR no resgate de previdência?", "manual_previdencia"),
    ("Quem recebe a indenização do seguro de vida?", "manual_vida"),
    ("O prestamista protege o titular do crédito?", "manual_prestamista"),
    ("O resgate parcial é permitido na previdência?", "manual_previdencia"),
    ("A indenização do seguro de vida é isenta de IR?", "manual_vida"),
    ("A cobertura do prestamista é limitada ao saldo devedor?", "manual_prestamista"),
    ("A morte acidental dobra o valor do seguro de vida?", "manual_vida"),
]


def _build_pipeline():
    chunker = TextChunker(chunk_size=256, chunk_overlap=32)
    embedder = EmbeddingService()
    store = LocalFAISSStore(embedder.dimension)
    pipeline = RAGPipeline(chunker, embedder, store)
    for fonte, texto in CORPUS.items():
        pipeline.ingest(texto, metadata={"fonte": fonte, "documento": fonte})
    return pipeline


def test_top3_contem_fonte_esperada():
    pipeline = _build_pipeline()
    acertos = 0
    for pergunta, fonte_esperada in PERGUNTAS_ESPERADAS:
        resultados = pipeline.retrieve(pergunta, k=3)
        fontes = [r.get("metadata", {}).get("fonte") for r in resultados]
        if fonte_esperada in fontes:
            acertos += 1
    # Critério de aceite: recall >= 90% no top-3 deste corpus controlado.
    assert acertos >= int(0.9 * len(PERGUNTAS_ESPERADAS)), f"recall={acertos}/{len(PERGUNTAS_ESPERADAS)}"


def test_retrieve_retorna_metadados_de_fonte():
    pipeline = _build_pipeline()
    resultados = pipeline.retrieve("carência para resgate", k=1)
    assert len(resultados) >= 1
    assert resultados[0]["metadata"]["fonte"] == "manual_previdencia"
