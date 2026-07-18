import os
from app.llm import LLMProvider, LLMResponse


class AnthropicLLM(LLMProvider):
    """LLM real via Anthropic Claude. Requer ANTHROPIC_API_KEY. TODO: testar manualmente com credencial real."""

    def __init__(self, model: str = "claude-3-5-sonnet-latest"):
        import anthropic
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import time
        start = time.time()
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        latency_ms = (time.time() - start) * 1000
        text = "".join(block.text for block in resp.content if block.type == "text")
        tp = resp.usage.input_tokens
        tc = resp.usage.output_tokens
        cost = (tp / 1000) * 0.003 + (tc / 1000) * 0.015
        return LLMResponse(text=text, tokens_prompt=tp, tokens_completion=tc,
                           latency_ms=latency_ms, cost_usd=cost, model=self.model)
