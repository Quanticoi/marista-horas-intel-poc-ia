# Inferência e aplicação no Jupyter

**08** solicita deploy e geração pela API. A versão precisa estar aprovada; o
worker executa inferência HTTP e persiste a proposta em PostgreSQL. O notebook
acompanha o job e salva `proposal_id` em `workspace/reports/v4-context.json`.

**09** usa esse contexto automaticamente, com opção de ID explícito. Consulta
`GET /v2/proposals/{id}/application-view`, valida schema/hash/paginação e exibe
ofertas com atividades filhas. Cada filtro consulta a API; não há SQL, treino ou
SDK MLflow/S3 no consumidor. Sem contexto, seleção ambígua exige escolha explícita.

Se o contexto perder apenas o ID da proposta, o 09 procura pela campanha atual,
comparando snapshot e conjunto exato de versões pela API. Uma correspondência
única é recuperada automaticamente. Se ainda não houve geração, apresenta
`AWAITING_GENERATION`, links para 07/08 e um seletor de propostas anteriores;
não interrompe com traceback nem escolhe uma proposta antiga silenciosamente.
Selecione uma proposta no controle e reexecute as células para consultá-la.

**10** pede a auditoria ao endpoint `/v2/audit/proposals/{id}`. Só considera VERIFIED
após confronto de fontes, snapshot, versões, runs, binários e manifests.

Nova campanha não reaproveita silenciosamente a proposta anterior. Execute 08 para
gerar a correspondente; repetir a mesma geração recupera seu job idempotente.
[Contrato HTTP v2](../contracts/academic_application_v2.md) · [Runbook](POC_V4_MANUAL_RUNBOOK.md).
