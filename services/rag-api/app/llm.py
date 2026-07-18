import abc
import os


class LLMResponse:
    def __init__(self, text: str, tokens_prompt: int = 0, tokens_completion: int = 0,
                 latency_ms: float = 0.0, cost_usd: float = 0.0, model: str = ""):
        self.text = text
        self.tokens_prompt = tokens_prompt
        self.tokens_completion = tokens_completion
        self.latency_ms = latency_ms
        self.cost_usd = cost_usd
        self.model = model


class LLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        ...


class LocalMockLLM(LLMProvider):
    """LLM determinístico para dev/CI sem custo.

    Recebe o contexto recuperado e produz uma resposta de grounding estável:
    repete o trecho mais relevante e cita a fonte. Quando não há contexto,
    recusa explicitamente (mitigação de alucinação).
    """

    def __init__(self, model: str = "mock-local"):
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import time
        start = time.time()

        # Extrai o contexto e a pergunta do user_prompt (formato definido em chat.py).
        ctx = ""
        pergunta = ""
        if "CONTEXTO:" in user_prompt and "PERGUNTA:" in user_prompt:
            partes = user_prompt.split("PERGUNTA:", 1)
            ctx = partes[0].replace("CONTEXTO:", "").strip()
            pergunta = partes[1].strip()

        if not ctx:
            resposta = (
                "Não encontrei essa informação nos documentos disponíveis. "
                "Por favor, consulte os canais oficiais da seguradora ou reformule a pergunta."
            )
        else:
            # Resposta determinística: parágrafo inicial do contexto + citação.
            trecho = ctx.split("\n\n")[0][:600].strip()
            resposta = (
                f"Com base nos documentos da seguradora:\n\n{trecho}\n\n"
                f"(Fonte: documentos internos de previdência/seguro)"
            )

        latency_ms = (time.time() - start) * 1000
        # Custo zero para mock.
        return LLMResponse(text=resposta, tokens_prompt=len(user_prompt)//4,
                           tokens_completion=len(resposta)//4, latency_ms=latency_ms,
                           cost_usd=0.0, model=self.model)


class AzureOpenAILLM(LLMProvider):
    """LLM real via Azure OpenAI. Requer AZURE_OPENAI_ENDPOINT e AZURE_OPENAI_API_KEY."""

    def __init__(self, model: str = "gpt-4o"):
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_API_KEY")
        deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", model)
        if not endpoint or not key:
            raise RuntimeError("Credenciais do Azure OpenAI não configuradas.")
        from openai import AzureOpenAI
        self.client = AzureOpenAI(api_version="2024-02-15-preview", azure_endpoint=endpoint, api_key=key)
        self.deployment = deployment
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import time
        start = time.time()
        resp = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        latency_ms = (time.time() - start) * 1000
        text = resp.choices[0].message.content or ""
        tp = resp.usage.prompt_tokens
        tc = resp.usage.completion_tokens
        # Tabela de preço estimada GPT-4o (USD/1k tokens). Ajuste conforme necessário.
        cost = (tp / 1000) * 0.005 + (tc / 1000) * 0.015
        return LLMResponse(text=text, tokens_prompt=tp, tokens_completion=tc,
                           latency_ms=latency_ms, cost_usd=cost, model=self.deployment)


def build_llm() -> LLMProvider:
    """Factory selecionando o provider via LLM_PROVIDER (default: local)."""
    kind = (os.getenv("LLM_PROVIDER") or "local").lower()
    if kind == "azure":
        return AzureOpenAILLM()
    if kind == "openai":
        # TODO: testar manualmente com OPENAI_API_KEY.
        from app.llm_openai import OpenAILLM
        return OpenAILLM()
    if kind == "anthropic":
        # TODO: testar manualmente com ANTHROPIC_API_KEY.
        from app.llm_anthropic import AnthropicLLM
        return AnthropicLLM()
    return LocalMockLLM()
