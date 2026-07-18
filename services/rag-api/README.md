# rag-api (Python / FastAPI)

Serviço central de IA: RAG, chat com grounding, agente, multiagentes, multimodal,
autenticação (Entra ID/RBAC) e dashboard de métricas.

## Rodar

```bash
python -m venv .venv && .venv/Scripts/Activate   # Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000
```

Testes: `pytest` (43 testes).

## Variáveis de ambiente principais

| Var | Padrão | Descrição |
|-----|--------|-----------|
| `VECTOR_STORE` | `local` | `local` (FAISS) ou `azure` (Azure AI Search) |
| `LLM_PROVIDER` | `local` | `local` (mock), `azure`, `openai`, `anthropic` |
| `VISION_PROVIDER` | `local` | `local` (mock OCR) ou `azure` (AI Vision) |
| `SCORE_MINIMO_GROUNDING` | `0.3` | Similaridade mínima para responder (senão recusa) |
| `ENTRA_TENANT_ID` / `ENTRA_AUDIENCE` | — | Auth Entra ID; tenant `00000000-...` ativa mock HS256 |

Sem nenhuma variável, o serviço roda 100% local sem custo.

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check |
| POST | `/documents/ingest` | Indexa documentos no vector store |
| GET | `/documents/count` | Total de chunks indexados |
| POST | `/retrieval/buscar` | Busca semântica (top-k) |
| POST | `/query` | RAG puro (retrieval + contexto) |
| POST | `/chat/perguntar` | Chat com grounding e recusa |
| POST | `/agente/executar` | Agente multi-step com ferramentas |
| GET | `/agente/execucoes/{id}` | Trace de execução do agente |
| POST | `/multiagente/executar` | Atendimento + revisor de Compliance |
| GET | `/multiagente/traces/{id}` | Trace do fluxo multiagente |
| POST | `/multimodal/extrair` | Extração de dados de imagens |
| GET | `/metrics` | Dashboard de métricas (requer usuário) |
| POST | `/admin/reindex` | Reindexação (requer admin) |

## Módulos

- `app/rag_pipeline.py`, `chunker.py`, `embeddings.py`, `vector_store.py` — RAG.
- `app/chat.py`, `llm.py` — chat e provedores de LLM.
- `app/agent.py`, `tools.py` — agente e ferramentas.
- `app/multiagent.py` — orquestração multiagente.
- `app/multimodal.py` — extração multimodal.
- `app/auth.py` — validação JWT Entra ID e RBAC.
