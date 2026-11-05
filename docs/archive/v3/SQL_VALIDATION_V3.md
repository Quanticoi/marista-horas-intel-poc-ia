> **HISTÓRICO — não executar como roteiro V4.** Consulte [a documentação atual](../../README.md). Treinamento operacional legado foi desativado.

# Conferência SQL V3

O banco de negócio é **planejamento_db**, schema **planning**. mlflow_db é administrado
exclusivamente pelo SDK/servidor MLflow; não execute DDL nem UPDATE nesse banco.
As consultas estão em [manual_validation_v3.sql](../../../sql/queries/manual_validation_v3.sql).
Não é necessário publicar PostgreSQL no host: o Jupyter já possui acesso read-only.

No notebook, copie os IDs do resultado atual e execute uma consulta por vez:

```python
from sqlalchemy import text
from src.workbench.journey_config import sql_engine
import pandas as pd
engine = sql_engine(cfg.source, cfg.timeout)
try:
    with engine.connect() as connection:
        table = pd.read_sql_query(text('''SELECT * FROM planning.v_model_inventory
            WHERE model_key=:model_key AND model_version=:version'''), connection,
            params={'model_key': params.model_name, 'version': params.model_version})
finally:
    engine.dispose()
display(table)
```

Selecione uma versão explícita; `params.model_version` não pode estar vazio.
Para demais consultas, passe `proposal_id`, `run_id`, `snapshot_id`, `campaign_id`
como parâmetros; `limit=100, offset=0`. Nada de concatenar input em SQL.

| View/tabela | Resultado esperado |
|---|---|
| v_model_inventory | Uma linha por versão catalogada, nome/contexto/hash/manifest; RECORDED não significa verificação viva |
| v_training_inventory | Job/tentativa/campanha, run/versão, métricas e erro sanitizado |
| v_proposal_lineage_readable | Uma linha por oferta, contribuições em array; não multiplicar oferta em JOIN N:N |
| proposal_model_usage | Uma contribuição por modelo/versão/run, com inference_id e line_keys |
| v_storage_manifest_inventory | Manifest do catálogo e três arquivos S3 reais, sem cópia de binários |
| proposal_generations + proposal_lines | row_count igual a count(l.*), IDs e quantidades iguais à API |

Três escopos DEMO com três disciplinas cada geram nove ofertas; o ensaio legado
agregado normalmente gera 90. Não aplicar a contagem de um cenário ao outro.
Versões anteriores sem catálogo 1.1 continuam acessíveis pelo Registry e pelas
tabelas de lineage/propostas. O agregador `/v1/audit/model` as classifica
LEGACY_PARTIAL quando faltam as evidências; nenhuma informação histórica é inventada.

SQL é autoridade de aprovação técnica auditada; alias champion precisa concordar.
Consulta de inventário não promove candidato. Verifique a integridade viva em
`GET /v1/audit/model?model_key=...&version=...` e `GET /v1/audit/proposal/{id}`.
