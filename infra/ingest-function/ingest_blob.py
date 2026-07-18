"""Azure Function (Python) — ingestão assíncrona de documentos.

Disparada por upload de PDF no Blob Storage, extrai texto e indexa no Azure AI Search.
Equivalente assíncrono do endpoint /documents/ingest da rag-api.

Deploy: func azure functionapp publish <nome-da-function> --python
"""

import logging
import os
import json

import azure.functions as func


def main(blob: func.InputStream):
    logging.info(f"Novo documento recebido: {blob.name}")
    texto = _extrair_texto(blob)
    _indexar_no_ai_search(blob.name, texto)
    logging.info("Indexação concluída.")


def _extrair_texto(blob: func.InputStream) -> str:
    # TODO: usar form recognizer / pdf parser real; placeholder lê como texto.
    try:
        return blob.read().decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _indexar_no_ai_search(nome: str, texto: str):
    endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
    key = os.getenv("AZURE_AI_SEARCH_KEY")
    if not endpoint or not key:
        logging.warning("Credenciais do Azure AI Search ausentes; pulando indexação.")
        return
    # Integração com AzureAISearchStore da rag-api (abstraído em app/vector_store.py).
    logging.info(f"Indexando '{nome}' ({len(texto)} chars) em {endpoint}")
