import abc
import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict

from app.tools import build_default_tools


@dataclass
class TraceStep:
    passo: int
    pensamento: str
    acao: str = ""
    entradas: dict = field(default_factory=dict)
    observacao: str = ""
    erro: bool = False


@dataclass
class Execution:
    id: str
    instrucao: str
    passos: list = field(default_factory=list)
    resposta_final: str = ""
    concluido: bool = False
    motivo_parada: str = ""
    timestamp: str = ""


class Planner(abc.ABC):
    """Decide o próximo passo do agente: qual tool chamar ou se deve responder."""

    @abc.abstractmethod
    def decide(self, instrucao: str, passos: list, tools: dict) -> dict:
        """Retorna {'acao': 'tool', 'tool': nome, 'entradas': {...}} ou
        {'acao': 'responder', 'resposta': texto}."""


class MockPlanner(Planner):
    """Planner determinístico para dev/CI e testes.

    Implementa a lógica de roteamento por intenção (sem LLM real):
    - pedido de resgate/previdência -> consultar_cliente -> consultar_apolices -> simular_resgate
    - pedido de documentos -> buscar_documentos
    - pedido de notificação -> enviar_notificacao
    """

    def decide(self, instrucao: str, passos: list, tools: dict) -> dict:
        texto = instrucao.lower()
        ja_feitos = [p.acao for p in passos if p.acao]

        if any(p in texto for p in ["resgate", "resgatar", "previdencia"]) and "consultar_cliente" not in ja_feitos:
            cid = _extrair_id(texto)
            return {"acao": "tool", "tool": "consultar_cliente", "entradas": {"cliente_id": cid}}

        if "consultar_cliente" in ja_feitos and "consultar_apolices" not in ja_feitos:
            cid = _extrair_id(texto)
            return {"acao": "tool", "tool": "consultar_apolices", "entradas": {"cliente_id": cid}}

        if "consultar_apolices" in ja_feitos and "simular_resgate" not in ja_feitos:
            aid = _extrair_id_apolice(texto)
            return {"acao": "tool", "tool": "simular_resgate", "entradas": {"apolice_id": aid or 1}}

        if any(p in texto for p in ["documento", "manual", "informa", "o que", "como"]) and "buscar_documentos" not in ja_feitos:
            return {"acao": "tool", "tool": "buscar_documentos", "entradas": {"pergunta": instrucao, "k": 3}}

        if "notificar" in texto and "enviar_notificacao" not in ja_feitos:
            return {"acao": "tool", "tool": "enviar_notificacao",
                    "entradas": {"canal": "email", "destinatario": "cliente@exemplo.com", "mensagem": instrucao}}

        return {"acao": "responder", "resposta": "Atendimento concluído com base nas ferramentas consultadas."}


def _extrair_id(texto: str) -> int:
    import re
    m = re.search(r"cliente\s*(?:id)?\s*(\d+)", texto)
    return int(m.group(1)) if m else 1


def _extrair_id_apolice(texto: str) -> int:
    import re
    m = re.search(r"apolice\s*(?:id)?\s*(\d+)", texto)
    return int(m.group(1)) if m else None


class LLMPlanner(Planner):
    """Planner baseado em LLM real (usado quando LLM_PROVIDER != local)."""

    def __init__(self, llm):
        self.llm = llm

    def decide(self, instrucao: str, passos: list, tools: dict) -> dict:
        tool_desc = "\n".join(f"- {t}: {tools[t].description}" for t in tools)
        historico = "\n".join(f"Passo {p.passo}: {p.acao} -> {p.observacao}" for p in passos)
        prompt = (
            "Você é um orquestrador de agente. Ferramentas disponíveis:\n"
            f"{tool_desc}\n\nInstrução do usuário: {instrucao}\n\n"
            f"Histórico:\n{historico}\n\n"
            "Responda APENAS um JSON: {\"acao\":\"tool\",\"tool\":\"<nome>\",\"entradas\":{...}} "
            "ou {\"acao\":\"responder\",\"resposta\":\"<texto>\"}."
        )
        resp = self.llm.generate("Você decide ações de agente em JSON.", prompt)
        try:
            return json.loads(resp.text)
        except Exception:
            return {"acao": "responder", "resposta": resp.text}


class AgentExecutor:
    def __init__(self, tools: dict | None = None, planner: Planner | None = None, max_steps: int = 6):
        self.tools = tools or build_default_tools()
        self.planner = planner or MockPlanner()
        self.max_steps = max_steps
        self._executions: dict[str, Execution] = {}

    def run(self, instrucao: str) -> Execution:
        exec_id = str(uuid.uuid4())[:8]
        execucao = Execution(id=exec_id, instrucao=instrucao,
                             timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        for i in range(1, self.max_steps + 1):
            decisao = self.planner.decide(instrucao, execucao.passos, self.tools)
            if decisao.get("acao") == "responder":
                execucao.resposta_final = decisao.get("resposta", "")
                execucao.concluido = True
                execucao.motivo_parada = "agente decidiu responder"
                break

            tool_nome = decisao.get("tool", "")
            entradas = decisao.get("entradas", {})
            passo = TraceStep(passo=i, pensamento=f"Chamar tool '{tool_nome}'", acao=tool_nome, entradas=entradas)
            if tool_nome not in self.tools:
                passo.erro = True
                passo.observacao = f"Tool '{tool_nome}' inexistente."
            else:
                try:
                    resultado = self.tools[tool_nome].run(**entradas)
                    passo.observacao = resultado.observacao
                    entradas["__resultado__"] = resultado.data
                except Exception as e:
                    passo.erro = True
                    passo.observacao = f"Erro: {e}"
            execucao.passos.append(passo)
        else:
            execucao.motivo_parada = f"limite de passos ({self.max_steps}) atingido"
            execucao.resposta_final = "Não foi possível concluir a tarefa no número máximo de passos."

        self._persistir(execucao)
        return execucao

    def get_execution(self, exec_id: str) -> Execution | None:
        return self._executions.get(exec_id)

    def _persistir(self, execucao: Execution):
        self._executions[execucao.id] = execucao
        try:
            os.makedirs("logs", exist_ok=True)
            with open(os.path.join("logs", "agentes_execucoes.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(execucao), ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass
