import json
import os
import time
from dataclasses import dataclass, field, asdict

from app.rag_pipeline import RAGPipeline
from app.llm import build_llm, LLMProvider

SCORE_MINIMO_GROUNDING = float(os.getenv("SCORE_MINIMO_GROUNDING", "0.3"))

SYSTEM_PROMPT = (
    "Você é um assistente corporativo de uma seguradora de vida e previdência. "
    "Responda APENAS com base no contexto fornecido. Se a informação não estiver "
    "no contexto, diga explicitamente que não sabe e não invente fatos. "
    "Cite a fonte (nome do documento) usada. Não dê conselho financeiro individualizado "
    "sem incluir um aviso de que se trata de informação educativa."
)


@dataclass
class InteractionLog:
    pergunta: str
    resposta: str
    fontes: list = field(default_factory=list)
    tokens_prompt: int = 0
    tokens_completion: int = 0
    latencia_ms: float = 0.0
    custo_usd: float = 0.0
    modelo: str = ""
    recusou: bool = False
    timestamp: str = ""


class ChatService:
    def __init__(self, pipeline: RAGPipeline, llm: LLMProvider | None = None):
        self.pipeline = pipeline
        self.llm = llm or build_llm()

    def _montar_user_prompt(self, pergunta: str, contexto: str) -> str:
        return f"CONTEXTO:\n{contexto}\n\nPERGUNTA: {pergunta}"

    def perguntar(self, pergunta: str, k: int = 3, historico: list | None = None) -> InteractionLog:
        historico = historico or []
        inicio = time.time()

        resultados = self.pipeline.retrieve(pergunta, k=k)
        contexto = "\n\n".join(
            f"[{item.get('metadata', {}).get('fonte', 'doc')}] {item['text']}" for item in resultados
        )

        recusou = False
        if not contexto or (resultados and all(item.get("score", 1.0) < SCORE_MINIMO_GROUNDING for item in resultados)):
            recusou = True
            user_prompt = self._montar_user_prompt(pergunta, "")
        else:
            user_prompt = self._montar_user_prompt(pergunta, contexto)

        resposta_llm = self.llm.generate(SYSTEM_PROMPT, user_prompt)

        fontes = [
            {
                "fonte": r.get("metadata", {}).get("fonte", "desconhecida"),
                "trecho": r["text"][:300],
                "score": r.get("score"),
            }
            for r in resultados
        ]

        log = InteractionLog(
            pergunta=pergunta,
            resposta=resposta_llm.text,
            fontes=fontes,
            tokens_prompt=resposta_llm.tokens_prompt,
            tokens_completion=resposta_llm.tokens_completion,
            latencia_ms=round(resposta_llm.latency_ms + (time.time() - inicio) * 1000, 2),
            custo_usd=resposta_llm.cost_usd,
            modelo=resposta_llm.model,
            recusou=recusou,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        self._persistir(log)
        return log

    def _persistir(self, log: InteractionLog):
        try:
            os.makedirs("logs", exist_ok=True)
            path = os.path.join("logs", "interacoes.jsonl")
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(log), ensure_ascii=False) + "\n")
        except Exception:
            # Logging não deve quebrar o fluxo principal.
            pass
