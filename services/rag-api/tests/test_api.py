from fastapi.testclient import TestClient

from app.main import app, store, pipeline
from app.agent import AgentExecutor, MockPlanner
from app.tools import Tool, ToolResult
from app.multiagent import MultiAgentOrchestrator, AttendanceAgent, ComplianceReviewer

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ingest_empty_text():
    resp = client.post("/documents/ingest", json={"text": ""})
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"]


def test_ingest_and_query_end_to_end():
    store.clear()

    text = (
        "A previdência privada é um tipo de investimento de longo prazo."
        " Existem dois planos principais: PGBL e VGBL."
        " No PGBL, o investidor pode deduzir até 12% da renda bruta anual."
        " No VGBL, o imposto incide apenas sobre os rendimentos."
    )
    resp = client.post("/documents/ingest", json={"text": text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["chunk_count"] > 0
    assert len(data["doc_ids"]) > 0

    resp = client.post("/query", json={"question": "o que é PGBL?"})
    assert resp.status_code == 200
    result = resp.json()
    assert "question" in result
    assert "answer" in result
    assert "sources" in result
    assert len(result["sources"]) > 0


def test_query_empty():
    resp = client.post("/query", json={"question": ""})
    assert resp.status_code == 400


def test_count():
    store.clear()
    client.post("/documents/ingest", json={"text": "conteudo teste"})
    resp = client.get("/documents/count")
    assert resp.status_code == 200
    assert resp.json()["total_chunks"] > 0


def test_chat_pergunta_dentro_do_escopo():
    store.clear()
    client.post("/documents/ingest", json={
        "text": "A previdência possui carência de 6 meses para resgate. O IR segue tabela regressiva.",
        "metadata": {"fonte": "manual_previdencia"},
    })
    resp = client.post("/chat/perguntar", json={"pergunta": "Qual a carência para resgate?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["recusou"] is False
    fontes = [f["fonte"] for f in data["fontes"]]
    assert "manual_previdencia" in fontes


def test_chat_pergunta_fora_do_escopo_recusa():
    store.clear()
    client.post("/documents/ingest", json={
        "text": "A previdência possui carência de 6 meses para resgate.",
        "metadata": {"fonte": "manual_previdencia"},
    })
    resp = client.post("/chat/perguntar", json={"pergunta": "Qual a capital da França?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["recusou"] is True


def test_retrieval_buscar_endpoint():
    store.clear()
    client.post("/documents/ingest", json={
        "text": "O seguro de vida cobre morte natural e acidental.",
        "metadata": {"fonte": "manual_vida"},
    })
    resp = client.post("/retrieval/buscar", json={"pergunta": "seguro de vida morte acidental", "k": 1})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["resultados"]) >= 1
    assert data["resultados"][0]["metadata"]["fonte"] == "manual_vida"


class _FakeTool(Tool):
    def __init__(self, name, data):
        self.name = name
        self.description = name
        self._data = data

    def run(self, **_):
        return ToolResult(ok=True, data=self._data, observacao=f"{self.name} ok")


def test_agente_executar_e_recuperar_trace(monkeypatch):
    tools = {
        "consultar_cliente": _FakeTool("consultar_cliente", {"id": 5}),
        "consultar_apolices": _FakeTool("consultar_apolices", {"apolices": []}),
        "simular_resgate": _FakeTool("simular_resgate", {"valorResgate": 10}),
    }
    agent = AgentExecutor(tools=tools, planner=MockPlanner(), max_steps=6)
    monkeypatch.setattr("app.main.agent_executor", agent)

    resp = client.post("/agente/executar", json={"instrucao": "resgate previdencia cliente id 5"})
    assert resp.status_code == 200
    exec_id = resp.json()["execucao_id"]

    resp2 = client.get(f"/agente/execucoes/{exec_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == exec_id


def test_multiagente_executar_e_trace(monkeypatch):
    orch = MultiAgentOrchestrator(
        AttendanceAgent(lambda i, t, p: ("Resposta com fonte. (Fonte: manual_vida)", ["manual_vida"])),
        ComplianceReviewer(),
        max_iteracoes=3,
    )
    monkeypatch.setattr("app.main.multi_orchestrator", orch)
    resp = client.post("/multiagente/executar", json={"instrucao": "o que é seguro de vida?"})
    assert resp.status_code == 200
    assert resp.json()["aprovado"] is True
    tid = resp.json()["id"]
    resp2 = client.get(f"/multiagente/traces/{tid}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == tid
