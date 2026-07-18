# Decisões Técnicas

Registro de escolhas não óbvias para recrutadores e mantenedores.

## 1. Orquestração de agentes: loop manual vs. LangGraph
**Escolha:** loop manual (pensar → tool → observar → responder) implementado em `app/agent.py`.
**Motivo:** demonstra domínio conceitual do ciclo de raciocínio e mantém o código legível e
sem dependências pesadas. LangGraph seria um atalho, mas esconderia o mecanismo. Um `LLMPlanner`
está previsto para usar LLM real quando configurado.

## 2. Vector store: FAISS local vs. Azure AI Search
**Escolha:** abstração `VectorStore` com `LocalFAISSStore` (default) e `AzureAISearchStore`.
**Motivo:** o projeto deve rodar 100% sem custo em dev/CI (FAISS), mas estar pronto para produção
Azure via variável `VECTOR_STORE=azure`.

## 3. LLM: mock local vs. Azure OpenAI/OpenAI/Anthropic
**Escolha:** `LocalMockLLM` determinístico por padrão; providers reais atrás de `LLM_PROVIDER`.
**Motivo:** testes de CI sem custo e determinísticos; integração real documentada e pronta.

## 4. Multimodal: OCR real vs. sidecar
**Escolha:** `LocalMockExtractor` com OCR (pytesseract) opcional + sidecar JSON; `AzureVisionExtractor` via GPT-4o.
**Motivo:** extração reproduzível em testes sem Tesseract instalado; caminho real documentado.

## 5. Autenticação: tokens Reais (RS256/JWKS) vs. HS256 local
**Escolha:** em produção valida RS256 via issuer/audience do Entra ID; em dev/testes usa HS256
com segredo local (tenant fake) para validar RBAC (401/403/200) sem tenant real.
**Motivo:** testes automatizados de autorização reproduzíveis.

## 6. Banco do sistema legado: SQLite
**Escolha:** SQLite via EF Core.
**Motivo:** zero infra em dev; trocável por Postgres em produção alterando a connection string.
