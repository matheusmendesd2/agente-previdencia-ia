# infra (Azure IaC — Bicep)

Infraestrutura como código para provisionar o ambiente Azure do projeto.

## Recursos (`main.bicep`)

- **Storage Account** — Blob para documentos enviados.
- **Azure AI Search** — vector store gerenciado (`VECTOR_STORE=azure`).
- **App Service** — hospeda a `rag-api`.
- **Function App** — ingestão assíncrona de PDFs do Blob (`ingest-function/ingest_blob.py`).
- **App Registration (Entra ID)** — appRoles `usuario` e `admin` para RBAC.

## Validar / implantar

```bash
az bicep build --file main.bicep          # validação estática
az deployment sub create --location brazilsouth --template-file main.bicep
```

> O `bicep build` roda no CI (job `validate_bicep`). Sem uma assinatura Azure, o projeto
> continua 100% funcional em modo local (FAISS + LLM mock).
