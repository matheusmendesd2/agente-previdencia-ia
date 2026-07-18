# PROGRESSO — Agente Previdência IA

Este arquivo é atualizado ao final de cada fase.

## Fase 0 — Setup e fundação ✅
- Monorepo com `services/{rag-api,legacy-api,notification-service}`, `agents`, `eval`, `finetuning`, `multimodal`, `infra`, `docs`.
- rag-api (FastAPI), legacy-api (.NET), notification-service (Node/Express) com `GET /health`.
- Dockerfile por serviço + `docker-compose.yml`.
- CI (GitHub Actions) builda os 3 serviços e roda health checks.
- Script `scripts/health-check.{ps1,sh}` validando 3/3.

## Fase 1 — API Legada (.NET/C#) ✅
- Entidades Cliente e Apolice; SQLite via EF Core.
- Endpoints: GET /clientes/{id}, GET /clientes/{id}/apolices, GET /apolices/{id}, POST /apolices/{id}/simulacao-resgate.
- Seed de 20 clientes fictícios. Swagger em /swagger.
- Testes: 23 (13 unit + 11 integração via WebApplicationFactory), incluindo 404.
- Ver `tests/LegacyApi.Tests` e `services/legacy-api/README.md`.

## Fase 2 — Notification Service (Node/TS) ✅
- Express + TypeScript, validação Zod.
- Endpoints: POST /notify, POST /upload (fila em memória + worker), GET /notify/queue.
- Testes: 10 (Jest + Supertest), incluindo validação de payload inválido.
- Ver `services/notification-service/README.md`.

## Fase 3 — RAG: ingestão, chunking, embeddings ✅
- Corpus sintético em `services/rag-api/data/documentos/` (manuais de seguro).
- Chunking por seção/parágrafo com overlap configurável (`app/chunker.py`).
- Embeddings locais via sentence-transformers (`all-MiniLM-L6-v2`) — modo dev sem custo.
- Vector store abstraído em interface `VectorStore` com `LocalFAISSStore` (default) e `AzureAISearchStore` (Azure AI Search), selecionável por `VECTOR_STORE`.
- Endpoints: POST /documents/ingest, POST /retrieval/buscar (top-k + score + fonte), POST /query.
- Testes: 19 (chunker, pipeline, vector store, API, regressão de retrieval com 10 perguntas — recall>=90% no top-3).
- `data/documentos/` deve ser populado (ver README do rag-api).

## Fase 4 — Geração LLM + Grounding ✅
- Endpoint POST /chat/perguntar: retrieval + prompt de grounding + histórico.
- Abstração LLMProvider com LocalMockLLM (default, gratuito/determístico), AzureOpenAILLM, OpenAI, Anthropic (documentados, fallback sem custo).
- Mitigação de alucinação: se o retrieval não atinge score mínimo (SCORE_MINIMO_GROUNDING, default 0.3), o sistema recusa ("não encontrei essa informação") em vez de inventar.
- Log de cada interação (pergunta, resposta, fontes, tokens, latência, custo estimado) em logs/interacoes.jsonl.
- Testes (rag-api): pergunta respondível cita fonte; pergunta fora de escopo recusa; log de custo/latência gravado; endpoints /chat e /retrieval/buscar. Total rag-api: 25 testes.
- LLM real (Azure/OpenAI/Anthropic) documentado com TODO de teste manual (não depende de credencial nos testes de CI).

## Fase 5 — Agente orquestrador (single agent com tools) ✅
- Loop de agente implementado manualmente (pensar → escolher tool → executar → observar → responder), demonstrando domínio conceitual (sem dependência de framework).
- Tools: buscar_documentos (RAG), consultar_cliente, consultar_apolices, simular_resgate (legacy-api), enviar_notificacao (notification-service).
- Endpoint POST /agente/executar (instrução em NL) e GET /agente/execucoes/{id} (trace auditável).
- Limite de passos (max_steps) para evitar loop infinito; trace de raciocínio persistido em logs/agentes_execucoes.jsonl.
- MockPlanner determinístico (dev/CI) + LLMPlanner (usa LLM real quando configurado).
- Testes: sequência esperada de tools (resgate), limite de passos com tool falhando, trace persistido/recuperável, endpoints. Total rag-api: 29 testes.

## Fase 6 — Multiagentes ✅
- Dois agentes especializados em processo único:
  - Agente de Atendimento: gera a resposta (via RAG/chat) e reformula quando reprovado.
  - Agente de Compliance/Revisão: valida promessa financeira indevida, citação de fonte e escopo (disclaimer).
- Ciclo de revisão: atendimento → compliance (reprovado) → reformula → compliance (aprovado). Máx 3 iterações.
- Endpoint POST /multiagente/executar + GET /multiagente/traces/{id}; trace completo persistido em logs/multiagente_traces.jsonl.
- Exemplo de trace legível em docs/exemplo-trace-multiagente.json.
- Testes: reprova 1ª e aprova 2ª tentativa; promessa indevida sempre barrada; trace persistido/consultável; endpoints. Total rag-api: 33 testes.

## Fase 7 — Multimodal ✅
- Endpoint POST /multimodal/extrair: recebe imagem (boleto/carteirinha/apólice) e devolve JSON estruturado.
- Extrator abstraído (MultimodalExtractor): LocalMockExtractor (sidecar JSON/OCR opcional via pytesseract) e AzureVisionExtractor (GPT-4o vision, documentado).
- Integrado como nova tool `extrair_imagem` do Agente de Atendimento.
- Fixtures sintéticos em app/documentos_teste (3 docs + sidecars) gerados por app/gerar_fixtures_multimodal.py.
- Testes: extração dos 3 documentos; imagem inexistente tratada graciosamente; upload via endpoint; rejeição de não-imagem. Total rag-api: 39 testes.

## Fase 8 — Fine-tuning de embeddings (em andamento)
- Pendente.

## Decisões técnicas
- Baseline das Fases 1-3 validado por testes existentes (23 + 10 + 19). Reconciliado e mantido.
- FAISS local como default para execução 100% gratuita; Azure AI Search implementado como alternativa documentada.
- DbSeeder excluído do critério de cobertura (é seed de dados, não lógica de negócio).
