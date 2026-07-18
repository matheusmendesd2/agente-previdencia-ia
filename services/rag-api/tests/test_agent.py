from app.agent import AgentExecutor, MockPlanner, TraceStep
from app.tools import Tool, ToolResult


class FakeTool(Tool):
    def __init__(self, name, resultado=None, falha=False):
        self.name = name
        self.description = f"fake {name}"
        self.resultado = resultado or {"ok": True}
        self.falha = falha

    def run(self, **kwargs):
        if self.falha:
            raise RuntimeError("tool sempre falha")
        return ToolResult(ok=True, data=self.resultado, observacao=f"{self.name} ok")


def test_sequencia_tools_resgate():
    tools = {
        "consultar_cliente": FakeTool("consultar_cliente", {"id": 5, "nome": "Ana"}),
        "consultar_apolices": FakeTool("consultar_apolices", {"apolices": [{"id": 9, "tipo": "Previdencia"}]}),
        "simular_resgate": FakeTool("simular_resgate", {"valorResgate": 1234.5}),
    }
    agent = AgentExecutor(tools=tools, planner=MockPlanner(), max_steps=6)
    execucao = agent.run("quero saber quanto resgataria da previdência, cliente id 5")
    acoes = [p.acao for p in execucao.passos]
    assert "consultar_cliente" in acoes
    assert "consultar_apolices" in acoes
    assert "simular_resgate" in acoes
    assert execucao.concluido is True


def test_limite_de_passos():
    # Tool que sempre falha: o agente não deve entrar em loop infinito.
    tools = {"consultar_cliente": FakeTool("consultar_cliente", falha=True)}
    agent = AgentExecutor(tools=tools, planner=MockPlanner(), max_steps=3)
    execucao = agent.run("resgate para cliente id 1")
    assert len(execucao.passos) <= 3
    # Não concluiu porque a única tool disponível falha.
    assert execucao.concluido is False
    assert "passos" in execucao.motivo_parada


def test_trace_persistido_e_recuperavel():
    tools = {"buscar_documentos": FakeTool("buscar_documentos", {"resultados": [{"text": "x"}]})}
    agent = AgentExecutor(tools=tools, planner=MockPlanner(), max_steps=6)
    execucao = agent.run("como funciona o seguro de vida")
    recuperada = agent.get_execution(execucao.id)
    assert recuperada is not None
    assert recuperada.id == execucao.id
    assert any(p.acao == "buscar_documentos" for p in recuperada.passos)
