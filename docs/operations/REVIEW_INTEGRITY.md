# Aprovação, integridade e serving

`TRAINED/VALIDATED` descreve o resultado científico. Aprovação exige revisão com
`OPERATOR_TOKEN`, versão explícita e motivo. A autoridade atual combina
`planning.model_approval_requests` e alias `champion` no MLflow.

O checkpoint SQL `RECONCILING` é persistido antes de alterar o alias. Enquanto SQL
e Registry não concordam, novas inferências falham de forma fechada. Em falha parcial,
inspecione o alias e retome o mesmo `approval_id`; não force estado direto no banco.
Mudança externa inesperada do alias não é sobrescrita silenciosamente.

Deploy V4 registra `academic_deployments`, ambiente POC, política PRELOAD/LAZY e
validade de 30 dias. Inferência confere aprovação, alias, snapshot e validade mesmo
quando o modelo está no cache. Revogação impede uso do cache aquecido. Inventário
de residência em `/v1/serving/runtime` informa carregamento, não autorização.

`GET /v2/audit/proposals/{id}` executa a conferência viva entre SQL, Registry e
RustFS. Um registro RECORDED não recebe VERIFIED apenas por existir no catálogo.
Checksum e assinatura são verificados antes da desserialização do modelo confiável.

[Governança no runbook](POC_V4_MANUAL_RUNBOOK.md) · [Lineage](../architecture/LINEAGE.md).
