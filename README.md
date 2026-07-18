# Agente Previdência IA

Sistema de IA generativa (RAG + Agentes + Multiagentes + Multimodal + Fine-tuning) que simula um assistente corporativo para uma empresa de seguros de vida e previdência.

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Agente Previdência IA                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   RAG API     │  │  Legacy API  │  │ Notification Svc │  │
│  │  (FastAPI)    │  │  (.NET/C#)   │  │  (Node.js)       │  │
│  │  Port 8000    │  │  Port 5000   │  │  Port 3000       │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Serviços

| Serviço | Tecnologia | Porta | Descrição |
|---------|-----------|-------|-----------|
| rag-api | Python/FastAPI | 8000 | Núcleo RAG + orquestração de agentes |
| legacy-api | .NET/C# 8 | 5000 | Sistema legado de clientes e apólices |
| notification-service | Node.js/Express | 3000 | Notificações e ingestão de documentos |

## Como Rodar

```bash
docker-compose up --build
```

Testar health checks:

```bash
curl http://localhost:8000/health
curl http://localhost:5000/health
curl http://localhost:3000/health
```
