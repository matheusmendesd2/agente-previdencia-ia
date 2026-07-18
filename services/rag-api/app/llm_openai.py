import os
from app.llm import LLMProvider, LLMResponse


class OpenAILLM(LLMProvider):
    """LLM real via OpenAI. Requer OPENAI_API_KEY. TODO: testar manualmente com credencial real."""

    def __init__(self, model: str = "gpt-4o-mini"):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import time
        start = time.time()
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            temperature=0,
        )
        latency_ms = (time.time() - start) * 1000
        text = resp.choices[0].message.content or ""
        tp = resp.usage.prompt_tokens
        tc = resp.usage.completion_tokens
        cost = (tp / 1000) * 0.00015 + (tc / 1000) * 0.0006
        return LLMResponse(text=text, tokens_prompt=tp, tokens_completion=tc,
                           latency_ms=latency_ms, cost_usd=cost, model=self.model)
