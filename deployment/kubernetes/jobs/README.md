Jobs são montados de forma estruturada em `deployment/scripts/common.ps1` e
`common.sh`, com nomes únicos, TTL, deadline, backoffLimit=0 e limites de recursos.
Bootstrap/migrate/buckets/backup/restore/E2E usam `poc-job` no namespace data;
treino/seed/validação/promoção usam `poc-runtime` em training. Nenhum Job recebe
permissão de executar comandos remotos arbitrários no dashboard.
