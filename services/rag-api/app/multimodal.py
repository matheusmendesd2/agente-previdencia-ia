import abc
import json
import os
from dataclasses import dataclass


@dataclass
class ExtracaoResult:
    sucesso: bool
    dados: dict
    texto_bruto: str = ""
    observacao: str = ""


class MultimodalExtractor(abc.ABC):
    @abc.abstractmethod
    def extrair(self, caminho_imagem: str) -> ExtracaoResult:
        ...


class LocalMockExtractor(MultimodalExtractor):
    """Extrator local sem custo.

    Estratégia (em ordem):
    1. Se pytesseract + Tesseract estiverem disponíveis, faz OCR real da imagem.
    2. Caso contrário, lê um arquivo sidecar '<imagem>.json' com os campos esperados
       (usado nos testes reproduzíveis e em dev).
    3. Fallback: heurística simples (Procura por padrões 'Campo: valor').
    """

    def extrair(self, caminho_imagem: str) -> ExtracaoResult:
        # 1. OCR real, se disponível.
        try:
            import pytesseract
            from PIL import Image
            texto = pytesseract.image_to_string(Image.open(caminho_imagem))
            if texto.strip():
                return ExtracaoResult(True, self._heuristic(texto), texto, "OCR via pytesseract")
        except Exception:
            pass

        # 2. Sidecar JSON.
        sidecar = caminho_imagem + ".json"
        if os.path.exists(sidecar):
            try:
                with open(sidecar, encoding="utf-8") as f:
                    dados = json.load(f)
                return ExtracaoResult(True, dados, json.dumps(dados), "sidecar JSON")
            except Exception:
                pass

        # 3. Fallback heurístico.
        return ExtracaoResult(False, {}, "", "sem OCR nem sidecar; não foi possível extrair")


    @staticmethod
    def _heuristic(texto: str) -> dict:
        dados = {}
        for linha in texto.splitlines():
            if ":" in linha:
                chave, _, valor = linha.partition(":")
                dados[chave.strip().lower().replace(" ", "_")] = valor.strip()
        return dados


class AzureVisionExtractor(MultimodalExtractor):
    """Extrator via Azure OpenAI GPT-4o vision. Requer credenciais.

    Documentado e pronto para uso; em dev/CI usamos LocalMockExtractor.
    """

    def __init__(self):
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_API_KEY")
        if not endpoint or not key:
            raise RuntimeError("Credenciais do Azure OpenAI não configuradas para visão.")
        from openai import AzureOpenAI
        self.client = AzureOpenAI(api_version="2024-02-15-preview", azure_endpoint=endpoint, api_key=key)
        self.deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o")

    def extrair(self, caminho_imagem: str) -> ExtracaoResult:
        import base64
        with open(caminho_imagem, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        resp = self.client.chat.completions.create(
            model=self.deployment,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extraia os campos estruturados (numero_apolice, valor, data_vencimento, nome_segurado) em JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                ],
            }],
            temperature=0,
        )
        texto = resp.choices[0].message.content or "{}"
        try:
            dados = json.loads(texto)
        except Exception:
            dados = {"texto_bruto": texto}
        return ExtracaoResult(True, dados, texto, "GPT-4o vision")


def build_extractor() -> MultimodalExtractor:
    if (os.getenv("VISION_PROVIDER") or "local").lower() == "azure":
        return AzureVisionExtractor()
    return LocalMockExtractor()
