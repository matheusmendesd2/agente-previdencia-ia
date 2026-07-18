import json
import os
import time
import uuid
from dataclasses import dataclass, field, asdict


@dataclass
class MensagemAgente:
    agente: str
    conteudo: str
    tipo: str = "mensagem"  # mensagem | revisao | resposta


@dataclass
class MultiAgentTrace:
    id: str
    instrucao: str
    mensagens: list = field(default_factory=list)
    aprovado: bool = False
    resposta_final: str = ""
    iteracoes: int = 0
    timestamp: str = ""


class ComplianceReviewer:
    """Agente de Compliance/Revisão.

    Valida a resposta do Agente de Atendimento antes de ir ao usuário:
    - contém promessa financeira indevida? (ex.: garantia de rentabilidade, valor exato não suportado)
    - cita fonte?
    - está dentro do escopo (não dá conselho financeiro individualizado sem disclaimer)?
    """

    PROMESSAS_INDEVIDAS = [
        "garanto", "rentabilidade garantida", "retorno certo", "lucro garantido",
        "100% de certeza", "valor fixo de", "você receberá exatamente",
    ]

    def revisar(self, resposta: str, fontes: list | None = None) -> dict:
        problemas = []
        texto = resposta.lower()

        for p in self.PROMESSAS_INDEVIDAS:
            if p in texto:
                problemas.append(f"promessa financeira indevida: '{p}'")

        if not fontes:
            # Resposta deve citar uma fonte (documento) quando baseada em RAG.
            if "não encontrei" not in texto and "documento" not in texto:
                problemas.append("resposta sem citação de fonte")

        if "conselho" in texto and "não é recomendação" not in texto and "educativa" not in texto:
            problemas.append("conserto financeiro individualizado sem disclaimer")

        aprovado = len(problemas) == 0
        parecer = "APROVADO" if aprovado else "REPROVADO: " + "; ".join(problemas)
        return {"aprovado": aprovado, "parecer": parecer, "problemas": problemas}


class AttendanceAgent:
    """Agente de Atendimento. Gera a resposta inicial e reformula quando reprovado."""

    def __init__(self, gerador):
        # gerador(instrucao, tentativa) -> (texto_resposta, fontes)
        self.gerador = gerador

    def gerar(self, instrucao: str, tentativa: int, problemas_anteriores: list | None = None) -> tuple:
        return self.gerador(instrucao, tentativa, problemas_anteriores or [])


class MultiAgentOrchestrator:
    def __init__(self, attendance: AttendanceAgent, compliance: ComplianceReviewer,
                 max_iteracoes: int = 3):
        self.attendance = attendance
        self.compliance = compliance
        self.max_iteracoes = max_iteracoes
        self._traces: dict[str, MultiAgentTrace] = {}

    def executar(self, instrucao: str) -> MultiAgentTrace:
        trace = MultiAgentTrace(
            id=str(uuid.uuid4())[:8],
            instrucao=instrucao,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        problemas = []
        for tentativa in range(1, self.max_iteracoes + 1):
            trace.iteracoes = tentativa
            resposta, fontes = self.attendance.gerar(instrucao, tentativa, problemas)
            trace.mensagens.append(MensagemAgente("atendimento", resposta, "resposta").__dict__)

            parecer = self.compliance.revisar(resposta, fontes)
            trace.mensagens.append(MensagemAgente("compliance", parecer["parecer"], "revisao").__dict__)

            if parecer["aprovado"]:
                trace.aprovado = True
                trace.resposta_final = resposta
                break
            problemas = parecer["problemas"]

        if not trace.aprovado:
            # Esgotou iterações: mantém última resposta com aviso de não conformidade.
            trace.resposta_final = "[NÃO CONFORMIDADE] " + (trace.mensagens[-2]["conteudo"] if len(trace.mensagens) >= 2 else "")

        self._persistir(trace)
        return trace

    def get_trace(self, trace_id: str) -> MultiAgentTrace | None:
        return self._traces.get(trace_id)

    def _persistir(self, trace: MultiAgentTrace):
        self._traces[trace.id] = trace
        try:
            os.makedirs("logs", exist_ok=True)
            with open(os.path.join("logs", "multiagente_traces.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(trace), ensure_ascii=False, default=str) + "\n")
        except Exception:
            pass
