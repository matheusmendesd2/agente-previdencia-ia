# Relatório de Avaliação de Qualidade

Modelo de geração: **mock-local**
Total de perguntas: 30 (respondivéis: 20, fora de escopo: 5, ambíguas: 5)

## Métricas agregadas

| Métrica | Valor |
|---------|-------|
| Recall@3 do retrieval | 95.00% |
| Faithfulness/Groundedness | 100.00% |
| Answer relevancy | 100.00% |
| Taxa de recusa correta (fora de escopo) | 40.00% |
| Ambíguas tratadas sem erro | 100.00% |

## Detalhe — perguntas respondíveis

| Pergunta | Recall | Grounded | Relevante | Fonte esperada | Fontes |
|----------|--------|----------|-----------|-----------------|--------|
| Qual é a carência para resgate na previdência? | ✅ | ✅ | ✅ | manual_previdencia | manual_previdencia, manual_vida, manual_vida |
| O seguro de vida cobre morte acidental? | ✅ | ✅ | ✅ | manual_vida | manual_vida, manual_vida, manual_vida |
| Como funciona o IR no resgate de previdência? | ✅ | ✅ | ✅ | manual_previdencia | manual_previdencia, manual_previdencia, manual_vida |
| O que faz o seguro prestamista? | ✅ | ✅ | ✅ | manual_prestamista | manual_prestamista, manual_previdencia, manual_prestamista |
| A indenização do seguro de vida é isenta de IR? | ✅ | ✅ | ✅ | manual_vida | manual_vida, manual_vida, manual_vida |
| O resgate parcial é permitido na previdência? | ✅ | ✅ | ✅ | manual_previdencia | manual_previdencia, manual_previdencia, manual_prestamista |
| A cobertura do prestamista é limitada ao saldo devedor? | ✅ | ✅ | ✅ | manual_prestamista | manual_prestamista, manual_prestamista, manual_previdencia |
| A morte acidental dobra o valor do seguro de vida? | ✅ | ✅ | ✅ | manual_vida | manual_vida, manual_vida, manual_vida |
| Qual a carência para o seguro prestamista? | ❌ | ✅ | ✅ | manual_prestamista | manual_previdencia, manual_vida, manual_vida |
| O plano de previdência permite portabilidade? | ✅ | ✅ | ✅ | manual_previdencia | manual_previdencia, manual_previdencia, manual_prestamista |
| Qual o prêmio do seguro prestamista? | ✅ | ✅ | ✅ | manual_prestamista | manual_prestamista, manual_prestamista, manual_vida |
| Quantos beneficiários pode ter o seguro de vida? | ✅ | ✅ | ✅ | manual_vida | manual_vida, manual_vida, manual_vida |
| O que é a tabela regressiva de IR? | ✅ | ✅ | ✅ | manual_previdencia | manual_previdencia, manual_previdencia, manual_prestamista |
| A previdência tem rendimento composto? | ✅ | ✅ | ✅ | manual_previdencia | manual_previdencia, manual_previdencia, manual_vida |
| Em caso de invalidez permanente, o prestamista quita a dívida? | ✅ | ✅ | ✅ | manual_prestamista | manual_prestamista, manual_prestamista, manual_previdencia |
| Qual o prazo de pagamento da indenização do seguro de vida? | ✅ | ✅ | ✅ | manual_vida | manual_vida, manual_vida, manual_prestamista |
| Apos 60 meses, qual a alíquota de IR no resgate? | ✅ | ✅ | ✅ | manual_previdencia | manual_previdencia, manual_previdencia, manual_previdencia |
| O seguro de vida tem carência para morte natural? | ✅ | ✅ | ✅ | manual_vida | manual_vida, manual_vida, manual_vida |
| O que é a portabilidade da previdência? | ✅ | ✅ | ✅ | manual_previdencia | manual_previdencia, manual_vida, manual_previdencia |
| Quem pode ser beneficiário do seguro de vida? | ✅ | ✅ | ✅ | manual_vida | manual_vida, manual_vida, manual_vida |

## Detalhe — fora de escopo (deve recusar)

- Qual a capital da França?: RECUSOU ✅
- Como investir em Bitcoin?: RECUSOU ✅
- Qual a receita do bolo de fubá?: NÃO RECUSOU ❌
- Quem ganhou a Copa do Mundo de 2022?: NÃO RECUSOU ❌
- Qual a melhor marca de carro?: NÃO RECUSOU ❌

