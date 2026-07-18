# Arquitetura — Agente Previdência IA

## Visão geral (Mermaid)

```mermaid
flowchart LR
    U[Usuário / Chat] -->|HTTP| RAG[rag-api\nFastAPI\nRAG + Agentes + Multimodal]
    U -->|upload PDF| NOT[notification-service\nNode/TS\nupload + notificações]
    U -->|consultas cliente| LEG[legacy-api\n.NET/C#\nclientes/apólices]

    RAG -->|buscar_documentos| RAG
    RAG -->|consultar_cliente / apolices / simular_resgate| LEG
    RAG -->|enviar_notificacao| NOT
    RAG -->|embeddings| EMB[(sentence-transformers\nFAISS local / Azure AI Search)]
    RAG -->|extrair_imagem| MULT[Imagem/PDF\nGPT-4o vision (mock local)]

    NOT -->|salva PDF| BLOB[(Azure Blob Storage)]
    BLOB -->|trigger| FN[Azure Function\ningestão assíncrona]
    FN --> EMB

    RAG -. autenticação / RBAC .-> ENT[Microsoft Entra ID\nusuário / admin]
    RAG -->|métricas| DASH[/metrics\ndashboard]
```

## Componentes e onde rodam

| Componente | Tecnologia | Azure |
|-----------|-----------|-------|
| rag-api | Python / FastAPI | Azure App Service |
| legacy-api | .NET / ASP.NET Core | App Service (ou container) |
| notification-service | Node.js / Express + TS | App Service (ou container) |
| ingestão assíncrona | Azure Function (Python) | Function App |
| documentos originais | — | Azure Blob Storage |
| vector database | FAISS local (dev) / Azure AI Search (prod) | Azure AI Search |
| auth / RBAC | JWT Bearer | Microsoft Entra ID |

## Fluxo de dados (exemplo: pergunta de resgate)

1. Usuário envia "quanto resgato da previdência? cliente id 5" ao rag-api (`/agente/executar`).
2. Agente de Atendimento decide chamar `consultar_cliente(5)` → legacy-api.
3. Decide `consultar_apolices(5)` → legacy-api.
4. Decide `simular_resgate(<id>)` → legacy-api.
5. Resposta gerada é revisada pelo Agente de Compliance (cita fonte? sem promessa indevida?).
6. Trace completo persistido e auditável; métricas expostas em `/metrics`.

## Decisões técnicas

Ver [`docs/decisoes-tecnicas.md`](decisoes-tecnicas.md).
