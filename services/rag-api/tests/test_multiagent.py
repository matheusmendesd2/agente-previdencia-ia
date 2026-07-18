from app.multiagent import MultiAgentOrchestrator, AttendanceAgent, ComplianceReviewer


def _gerador_promessa_indevida(instrucao, tentativa, problemas):
    if tentativa == 1:
        # 1ª tentativa: contém promessa indevida e sem fonte.
        return "Garanto que você terá 100% de certeza de rentabilidade garantida de R$ 5.000.", []
    # 2ª tentativa: reformulada com disclaimer e fonte.
    return ("Com base nos documentos, o resgate segue a tabela regressiva. (Fonte: manual_previdencia. "
            "Informação educativa, não é recomendação financeira.)", ["manual_previdencia"])


def test_compliance_reprova_primeira_e_aprova_segunda():
    orch = MultiAgentOrchestrator(
        AttendanceAgent(_gerador_promessa_indevida),
        ComplianceReviewer(),
        max_iteracoes=3,
    )
    trace = orch.executar("quanto resgato?")
    assert trace.aprovado is True
    assert trace.iteracoes == 2
    # Deve haver ao menos 1 reprovação e 1 aprovação no histórico.
    pareceres = [m for m in trace.mensagens if m["tipo"] == "revisao"]
    assert any("REPROVADO" in p["conteudo"] for p in pareceres)
    assert any("APROVADO" in p["conteudo"] for p in pareceres)


def test_promessa_indevida_sempre_barrada():
    reviewer = ComplianceReviewer()
    r = reviewer.revisar("Garanto rentabilidade garantida de 10% ao ano.", [])
    assert r["aprovado"] is False
    assert any("promessa" in p for p in r["problemas"])


def test_trace_multiagente_persistido_e_consultavel():
    orch = MultiAgentOrchestrator(
        AttendanceAgent(lambda i, t, p: ("Resposta com fonte. (Fonte: manual_vida)", ["manual_vida"])),
        ComplianceReviewer(),
        max_iteracoes=3,
    )
    trace = orch.executar("o que é seguro de vida?")
    recuperado = orch.get_trace(trace.id)
    assert recuperado is not None
    assert recuperado.id == trace.id
    assert recuperado.aprovado is True
    assert any(m["agente"] == "compliance" for m in recuperado.mensagens)
