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

### Próximas Fases
- FASE 1: API Legada com dados de clientes e apólices
- FASE 2: Serviço Node.js com notificações e upload
- FASE 3: Pipeline RAG (chunking, embeddings, retrieval)
