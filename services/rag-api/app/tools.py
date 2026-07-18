import abc
import json
import os
from dataclasses import dataclass


@dataclass
class ToolResult:
    ok: bool
    data: dict
    observacao: str


class Tool(abc.ABC):
    name: str = ""
    description: str = ""

    @abc.abstractmethod
    def run(self, **kwargs) -> ToolResult:
        ...


class HttpToolBase(Tool):
    def __init__(self, base_url: str = ""):
        self.base_url = base_url or os.getenv("LEGACY_API_URL", "http://localhost:8080")


class BuscarDocumentosTool(Tool):
    """Busca chunks relevantes no RAG (via endpoint /retrieval/buscar)."""
    name = "buscar_documentos"
    description = "Busca trechos relevantes nos documentos da seguradora para uma pergunta."

    def __init__(self, rag_base_url: str = ""):
        self.base_url = rag_base_url or os.getenv("RAG_API_URL", "http://localhost:8000")

    def run(self, pergunta: str = "", k: int = 3, **_):
        import requests
        resp = requests.post(f"{self.base_url}/retrieval/buscar",
                             json={"pergunta": pergunta, "k": k}, timeout=30)
        resp.raise_for_status()
        return ToolResult(ok=True, data=resp.json(), observacao=f"Recuperados {len(resp.json().get('resultados', []))} chunks.")


class ConsultarClienteTool(HttpToolBase):
    name = "consultar_cliente"
    description = "Consulta os dados de um cliente pelo id."

    def run(self, cliente_id: int = 0, **_):
        import requests
        resp = requests.get(f"{self.base_url}/clientes/{cliente_id}", timeout=30)
        if resp.status_code == 404:
            return ToolResult(ok=False, data={}, observacao="Cliente não encontrado.")
        resp.raise_for_status()
        return ToolResult(ok=True, data=resp.json(), observacao=f"Cliente {cliente_id} encontrado.")


class ConsultarApolicesTool(HttpToolBase):
    name = "consultar_apolices"
    description = "Lista as apólices de um cliente pelo id."

    def run(self, cliente_id: int = 0, **_):
        import requests
        resp = requests.get(f"{self.base_url}/clientes/{cliente_id}/apolices", timeout=30)
        if resp.status_code == 404:
            return ToolResult(ok=False, data={}, observacao="Cliente não encontrado.")
        resp.raise_for_status()
        return ToolResult(ok=True, data={"apolices": resp.json()}, observacao=f"{len(resp.json())} apólices.")


class SimularResgateTool(HttpToolBase):
    name = "simular_resgate"
    description = "Simula o valor de resgate de uma apólice de previdência pelo id."

    def run(self, apolice_id: int = 0, data_referencia: str = "", **_):
        import requests
        url = f"{self.base_url}/apolices/{apolice_id}/simulacao-resgate"
        if data_referencia:
            url += f"?dataReferencia={data_referencia}"
        resp = requests.post(url, timeout=30)
        if resp.status_code == 404:
            return ToolResult(ok=False, data={}, observacao="Apólice não encontrada.")
        resp.raise_for_status()
        return ToolResult(ok=True, data=resp.json(), observacao="Simulação de resgate concluída.")


class EnviarNotificacaoTool(Tool):
    name = "enviar_notificacao"
    description = "Envia uma notificação (e-mail/SMS) para um destinatário."

    def __init__(self, notify_base_url: str = ""):
        self.base_url = notify_base_url or os.getenv("NOTIFY_API_URL", "http://localhost:3000")

    def run(self, canal: str = "email", destinatario: str = "", mensagem: str = "", **_):
        import requests
        resp = requests.post(f"{self.base_url}/notify",
                             json={"canal": canal, "destinatario": destinatario, "mensagem": mensagem},
                             timeout=30)
        if resp.status_code >= 400:
            return ToolResult(ok=False, data={}, observacao="Falha ao enviar notificação.")
        return ToolResult(ok=True, data=resp.json(), observacao="Notificação enfileirada.")


class ExtrairImagemTool(Tool):
    name = "extrair_imagem"
    description = "Extrai dados estruturados (número da apólice, valor, vencimento) de uma imagem/documento escaneado."

    def __init__(self, extractor=None):
        self.extractor = extractor

    def run(self, caminho_imagem: str = "", **_):
        if not caminho_imagem:
            return ToolResult(ok=False, data={}, observacao="caminho_imagem obrigatório.")
        extrator = self.extractor
        if extrator is None:
            from app.multimodal import build_extractor
            extrator = build_extractor()
        res = extrator.extrair(caminho_imagem)
        return ToolResult(ok=res.sucesso, data=res.dados, observacao=res.observacao)


def build_default_tools() -> dict:
    return {
        t.name: t for t in [
            BuscarDocumentosTool(),
            ConsultarClienteTool(),
            ConsultarApolicesTool(),
            SimularResgateTool(),
            EnviarNotificacaoTool(),
            ExtrairImagemTool(),
        ]
    }
