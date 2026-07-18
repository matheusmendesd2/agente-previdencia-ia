# notification-service (Node.js / TypeScript)

Serviço de notificações e upload de documentos. Express + TypeScript, validação com Zod,
upload via Multer e fila de notificações em memória.

## Rodar

```bash
npm install
npm run build
npm start          # http://localhost:3000
```

Dev: `npm run dev`. Testes: `npm test` (10 testes, Jest).

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check |
| POST | `/notify` | Enfileira uma notificação (validada com Zod) |
| GET | `/notify/queue` | Lista a fila de notificações |
| POST | `/upload` | Upload de arquivo (multipart, Multer) |

## Estrutura

- `index.ts` — app Express e rotas.
- `src/` — schemas Zod e handlers.
- `dist/` — saída compilada (`tsc`).
