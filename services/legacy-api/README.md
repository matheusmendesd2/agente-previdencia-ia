# legacy-api (.NET 8 / C#)

Simula o sistema legado corporativo de clientes, apólices e simulação de resgate de
previdência. ASP.NET Core Minimal API + EF Core (SQLite) com seed de 20 clientes.

## Rodar

```bash
dotnet run          # http://localhost:8080
```

Swagger em `/swagger`. Testes: `dotnet test ../../tests/LegacyApi.Tests` (23 testes).

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Health check |
| GET | `/clientes/{id}` | Dados do cliente |
| GET | `/clientes/{id}/apolices` | Apólices do cliente |
| GET | `/apolices/{id}` | Detalhe de uma apólice |
| POST | `/apolices/{id}/simulacao-resgate` | Simula o valor de resgate |

## Estrutura

- `Program.cs` — endpoints e configuração.
- `Models/`, `Data/AppDbContext.cs` — entidades e contexto EF Core.
- `Services/ResgateService.cs` — regra de negócio da simulação.
- Banco SQLite criado e populado automaticamente na inicialização.
