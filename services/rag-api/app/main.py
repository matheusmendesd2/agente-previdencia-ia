from fastapi import FastAPI

app = FastAPI(title="RAG API - Agente Previdência IA")

@app.get("/health")
async def health():
    return {"status": "ok"}
