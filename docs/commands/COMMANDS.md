# Comandos atuais

Execute na raiz. No Windows configure DOCKER_CONTEXT=desktop-linux.

| Operação | Comando |
|---|---|
| Build | docker compose build mlflow jupyter |
| Subir | docker compose up -d --wait --wait-timeout 300 |
| Status | docker compose ps -a |
| Logs | docker compose logs -f --tail 100 api |
| Parar | docker compose stop |
| Seed | docker compose run --rm tools seed |
| Treinar | docker compose run --rm tools train |
| Retreinar | docker compose run --rm tools retrain SNAPSHOT |
| Aprovar | docker compose run --rm tools promote CHAVE VERSAO OPERADOR "MOTIVO" |
| Migrar schemas | .\deployment\scripts\compose.ps1 migrate |
| Publicar API por modelo | .\deployment\scripts\compose.ps1 publish -ModelKey CHAVE |
| Reconciliar | docker compose run --rm tools reconcile CHAVE OPERADOR "MOTIVO" |
| Prever | docker compose run --rm tools predict CICLO SNAPSHOT CHAVE |
| Avaliar | docker compose run --rm tools evaluate CICLO |
| Monitor | docker compose run --rm tools monitor |
| Recuperar jobs | docker compose run --rm tools recover |
| E2E | docker compose run --rm tools e2e |
| Backup | docker compose run --rm tools backup |
| Restore isolado | docker compose run --rm tools restore backups/IDENTIFICADOR restore_verificacao |

Validação diária: deployment/scripts/compose.ps1 validate.
E2E exige 30 champions compatíveis e APIs publicadas. Treinar não promove modelos.
Depois da publicação, comandos Docker de ciclo de vida precisam de
`-f compose.yaml -f .runtime/models.compose.json`; compose.ps1 inclui ambos automaticamente.
[Notebook, entrada de dados e publicação C3](../operations/C3_TRAINING.md).
