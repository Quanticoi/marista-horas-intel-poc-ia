# MLflow

[Tutorial da interface](MLFLOW_TUTORIAL.md). Tracking/Registry em mlflow_db;
artefatos em RustFS. Worker único e limite 2GiB no Compose.
Servidor postgresql+psycopg2 para compatibilidade de versões string no Registry.

`docker compose run --rm tools promote CHAVE VERSAO OPERADOR "MOTIVO"` faz aprovação
 auditada. reconcile corrige divergência DB/alias. Não há transação distribuída.
Modelos públicos não entram no catálogo acadêmico. Não publicar sem autenticação.

[Fluxo C3 atual](C3_TRAINING.md): o SDK envia arquivos diretamente ao RustFS
(`--no-serve-artifacts`). Promoção exige bundle binário 2.0 com integridade conferida;
versões JSON antigas são preservadas, mas precisam de retreinamento para publicação.
`compose.ps1 publish -ModelKey CHAVE` publica a versão aprovada num servidor dedicado.
Nova aprovação requer republicação; até lá a API anterior rejeita o deployment revogado.
Migração de schema: `compose.ps1 migrate`, após backup, antes de atualizar o servidor.
