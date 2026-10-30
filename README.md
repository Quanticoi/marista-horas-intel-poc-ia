# Marista — jornada completa Planilha Turmas

POC executada **100% em Docker Desktop / Docker Compose, sem Rancher**.
A jornada usa dados sintéticos declarados: SQL → preparação → treinamento →
MLflow Tracking/Registry → RustFS → inferência → proposta PostgreSQL → API.
As métricas DEMO não representam qualidade em dados institucionais.

## Executar

Com Docker Desktop ativo, na raiz do repositório:

```powershell
.\deployment\scripts\compose.ps1 rebuild
.\deployment\scripts\compose.ps1 acceptance
```

O `.env` existente deve ser preservado junto dos volumes. Para instalação nova,
use `compose.ps1 init`. Para uso diário, `start`, `status`, `journey` e `stop`.
O rebuild aplica migrations e preserva dados; `acceptance` verifica a mesma
execução após reinício do MLflow e após outro rebuild.

Abra [Jupyter](http://127.0.0.1:8888/lab/tree/notebooks/01_jornada_completa_planilha_turmas.ipynb)
e execute **Restart Kernel and Run All** no notebook principal:
[01_jornada_completa_planilha_turmas.ipynb](notebooks/01_jornada_completa_planilha_turmas.ipynb).
`templates/` mostra o arquivo versionado; `workspace/notebooks/` guarda suas cópias
editáveis, preservadas nas atualizações.

## Interfaces

| Interface | Acesso | Credencial no `.env` |
|---|---|---|
| Jupyter | http://127.0.0.1:8888/lab | JUPYTER_TOKEN |
| MLflow | http://127.0.0.1:5000 | Sem login nesta POC local |
| API | http://127.0.0.1:8000/docs | API_TOKEN |
| Entrada de dados | http://127.0.0.1:8020/docs | INGESTION_TOKEN |
| Dashboard de logs | http://127.0.0.1:8088 | DASHBOARD_TOKEN |
| RustFS | http://127.0.0.1:9001 | AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY |
| RabbitMQ | http://127.0.0.1:15672 | poc / RABBITMQ_PASSWORD |

## Dados e evidências

- PostgreSQL `mlflow_db`: metadados de tracking e Registry, gerenciados pelo MLflow.
- PostgreSQL `planejamento_db.planning`: fonte DEMO, catálogo, propostas e metadados operacionais.
- RustFS, bucket `pucpr-poc`: modelos e artefatos; jornada usa proxy MLflow.
- `artifacts/reports`: notebook executado, resumo e relatórios de testes reais.
- `data/compose-logs`: eventos sanitizados consultáveis no dashboard por correlation_id.
- [history/state.md](history/state.md) e [events.tsv](history/events.tsv): decisões, resultados e pendências.

[Guia da jornada](docs/operations/JOURNEY.md) contém configuração, SQL, API,
idempotência, mapeamento C3, diagnóstico e limites funcionais da demonstração.
A proposta é DRAFT e a regra de modulação é provisória; não há promoção automática.

O [fluxo anterior C3](docs/operations/C3_TRAINING.md), notebook 09 e aprovação/publicação
por modelo continuam disponíveis. Não são pré-requisitos para a jornada DRAFT.
Charts Kubernetes permanecem como referência histórica, fora do runtime e do aceite.

[Índice da documentação](docs/README.md) · [Backup](docs/operations/BACKUP_RESTORE.md).
Não usar `down -v`: isso remove volumes. Homologação funcional, produção e publicação
Git são etapas separadas; não estão implícitas no aceite técnico desta POC.