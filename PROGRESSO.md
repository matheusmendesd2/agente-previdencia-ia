# Progresso do Projeto

## FASE 0 — Setup e Fundação ✓

### O que foi feito
- Estrutura de diretórios do monorepo criada
- rag-api (Python/FastAPI) com endpoint GET /health
- legacy-api (.NET/C#) com endpoint GET /health
- notification-service (Node.js/Express) com endpoint GET /health
- Dockerfiles para cada serviço
- docker-compose.yml na raiz
- README inicial com arquitetura
- .gitignore configurado

### Decisões Técnicas
- FastAPI para rag-api: performance assíncrona, suporte nativo a OpenAPI
- .NET 8 minimal API: leve e moderna
- Node.js/Express + TypeScript: maturidade e tipagem
- Docker compose para orquestração local

## FASE 1 — API Legada ✓

### O que foi feito
- Entidades `Cliente` (Id, Nome, Documento, Email) e `Apólice` (Id, ClienteId, Numero, Tipo, Status, Valor, DataContratacao)
- EF Core + SQLite com `AppDbContext`
- 4 endpoints REST: GET /clientes/{id}, GET /clientes/{id}/apolices, GET /apolices/{id}, POST /apolices/{id}/simulacao-resgate
- `ResgateService` com regras de IR para previdência (tabela regressiva IR)
- Seed data: 12 clientes, 18 apólices (previdência e vida, ativas e canceladas)
- Swagger UI em desenvolvimento
- Projeto de testes com 13 unit tests (ResgateService) e 11 integration tests (endpoints)
- Solução (.sln) na raiz do repositório
- Testes usam `InMemoryDatabase` + `CustomWebApplicationFactory` com content root configurado

### Decisões Técnicas
- Testes em `tests/` com DLL Reference (não ProjectReference) devido a bug MSBuild 17.9.8
- `Program.Public.cs` partial class para expor `Program` ao `WebApplicationFactory`
- `InternalsVisibleTo` via AssemblyInfo.cs
- Post-build target copia `deps.json` e `runtimeconfig.json` para o diretório de saída dos testes
- `CustomWebApplicationFactory` override para configurar `ContentRoot` e substituir Sqlite por InMemory

## FASE 2 — Notification Service ✓

### O que foi feito
- `POST /notify` com validação de e-mail, assunto e mensagem — retorna 202 e enfileira
- `GET /notify/queue` com estatísticas da fila (total, pending, sent, failed)
- `POST /upload` com Multer para upload de CSV — valida extensão e retorna metadados
- Worker assíncrono processa notificações pendentes a cada 5s
- Serviço de fila em memória (`services/queue.ts`)
- 10 testes (health, notify, upload, queue stats)
- `stopWorker()` para limpeza entre testes

### Decisões Técnicas
- Multer para upload com `dest: /tmp/uploads`
- Fila em memória (simples e sem dependências externas)
- Worker via `setInterval` com cleanup em testes
- Export `app` para testes com Supertest; `app.listen` só em NODE_ENV !== 'test'

## FASE 3 — Pipeline RAG ✓

### O que foi feito
- `app/chunker.py`: TextChunker com chunk_size, chunk_overlap, corte em boundaries de palavra
- `app/embeddings.py`: EmbeddingService com `sentence-transformers/all-MiniLM-L6-v2`
- `app/vector_store.py`: VectorStore com FAISS IndexFlatL2 em memória
- `app/rag_pipeline.py`: RAGPipeline completo — ingest (chunk → embed → store) e query (embed → search → generate)
- `POST /documents/ingest`: recebe texto, chunking, embedding e armazenamento
- `POST /query`: pergunta com k resultados, retorna resposta + fontes
- `GET /documents/count`: total de chunks armazenados
- Mock LLM na RAGPipeline (contexto concatenado como resposta)
- `.dockerignore` para build eficiente da imagem

### Decisões Técnicas
- sentence-transformers + FAISS: tudo local, sem API keys
- Chunker com word-boundary e overlap para manter contexto entre chunks
- RAGPipeline._generate() usa template simples (mock), facilmente substituível por OpenAI/Ollama
- TestClient da FastAPI para testes de integração

## Próximas Fases
- FASE 4: Agentes e multi-agentes (LangGraph / CrewAI)
