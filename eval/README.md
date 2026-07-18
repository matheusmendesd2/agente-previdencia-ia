# eval (Framework de avaliação)

Avaliação automatizada da qualidade das respostas do RAG/chat, inspirada em
frameworks como RAGAS. Roda 100% local com o LLM mock.

## Rodar

```bash
python run_eval.py      # gera eval/relatorio.md
```

Testes: `pytest test_eval.py` (1 teste).

## Métricas

- **Faithfulness / Grounded** — resposta sustentada pelo contexto recuperado.
- **Answer relevancy** — aderência da resposta à pergunta.
- **Recall@3** — o documento correto está entre os 3 primeiros.
- **Refusal rate** — recusa correta quando não há base para responder.

## Arquivos

- `dataset.json` — 30 perguntas rotuladas (com casos de recusa esperada).
- `run_eval.py` — executa a avaliação e escreve o relatório.
- `relatorio.md` — resultados (Recall@3 95%, Grounded 100%, Recusa 40%).
