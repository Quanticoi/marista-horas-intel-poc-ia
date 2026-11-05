# Inferência e aplicação no Jupyter

**08** solicita deploy e geração pela API. A versão precisa estar aprovada; o
worker executa inferência HTTP e persiste a proposta em PostgreSQL. O notebook
acompanha o job e salva `proposal_id` em `workspace/reports/v4-context.json`.

**09** usa esse contexto automaticamente, com opção de ID explícito. Consulta
`GET /v2/proposals/{id}/application-view`, valida schema/hash/paginação e exibe
ofertas com atividades filhas. Cada filtro consulta a API; não há SQL, treino ou
SDK MLflow/S3 no consumidor. Sem contexto, seleção ambígua exige escolha explícita.

**10** pede a auditoria ao endpoint `/v2/audit/proposals/{id}`. Só considera VERIFIED
após confronto de fontes, snapshot, versões, runs, binários e manifests.

Nova campanha não reaproveita silenciosamente a proposta anterior. Execute 08 para
gerar a correspondente; repetir a mesma geração recupera seu job idempotente.
[Contrato HTTP v2](../contracts/academic_application_v2.md) · [Runbook](POC_V4_MANUAL_RUNBOOK.md).
