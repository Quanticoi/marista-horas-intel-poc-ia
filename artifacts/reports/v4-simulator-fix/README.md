# Simulador sem proposta selecionada — 05/11/2026

O contexto observado tinha uma nova campanha e `proposal_id=null`. As propostas
disponíveis pertenciam a ensaios anteriores. O notebook 07 salvo mostrava
INSPECT_ONLY; o 08 salvo não tinha execução registrada. O 09 encerrava com ValueError.

Correção: a API permite filtrar propostas por campanha, confrontando snapshot e
conjunto exato de versões. O cliente recupera automaticamente a correspondência
única. Sem geração, 09/10 mostram AWAITING_GENERATION/NOT_EXECUTED, instruções para
07/08 e um seletor explícito de propostas existentes. Não há geração ou aprovação
automática, nem escolha silenciosa da proposta mais recente.

Validação executada:

- [10 testes aprovados](selection-junit.xml): seleção, ambiguidade, recuperação,
  ausência de fallback e SQL filtrado por versões.
- [Notebook 09 com geração pendente](pending/09_simulador_aplicacao.executed.ipynb):
  kernel novo, orientação e seletor, sem traceback; consulta NOT_EXECUTED.
- [Notebook 09 com proposta explícita](selected/09_simulador_aplicacao.executed.ipynb):
  kernel novo, 70 ofertas e 107 origens pela API; paginação e P164 conferidos.
- [Resumo](proof.json), validação estática, lint e checagem de segredos aprovados.

As imagens API/Jupyter foram reconstruídas e aplicadas. Não houve novo treinamento,
aprovação, geração ou reset durante esta correção. O usuário iniciou outra campanha
durante a conferência; seu contexto não foi restaurado para um valor anterior.
Interação visual manual não foi presumida. Os notebooks 09/10 devem ser reabertos
para carregar as fontes atualizadas; cópias anteriores ficam no arquivo de notebooks.
