# Documentação V4

O roteiro atual usa Docker Compose e notebooks **00–11**. O treinamento ocorre no
Jupyter/Workbench; o worker operacional executa inferência e persistência.
Comece pelo [README do projeto](../README.md) ou pelo [runbook](operations/POC_V4_MANUAL_RUNBOOK.md).

| Preciso… | Documento |
|---|---|
| Instalar ou atualizar | [Windows](installation/WINDOWS.md), [Linux](installation/LINUX.md), [Compose](commands/DOCKER_COMPOSE.md) |
| Abrir os serviços | [Acessos e credenciais](operations/ACESSOS.md), [RustFS](operations/RUSTFS.md) |
| Executar e editar notebooks | [Jupyter](operations/JUPYTER.md), [catálogo](../notebooks/README.md), [jornada](operations/JOURNEY.md) |
| Entender os componentes | [Arquitetura](architecture/ARCHITECTURE.md), [fluxo de dados](architecture/DATA_FLOW.md), [mapa C3](operations/C3_TRAINING.md) |
| Organizar modelos e campanhas | [Organização MLflow](operations/MLFLOW_MODEL_ORGANIZATION.md), [repetição e Traces](operations/EXPERIMENTS_AND_TRACING.md) |
| Conferir uma execução | [MLflow](operations/MLFLOW_TUTORIAL.md), [PostgreSQL](operations/POSTGRES.md), [lineage](architecture/LINEAGE.md) |
| Consumir a proposta | [Contrato HTTP v2](contracts/academic_application_v2.md), [simulador HTTP](operations/INFERENCE_NOTEBOOK.md) |
| Limpar os ensaios e manter a origem | [Reset seletivo](operations/RESET_POC.md) |
| Revisar a entrega | [Aceite](operations/ACCEPTANCE.md), [revisão do repositório](REPOSITORY_REVIEW.md) |
| Resolver uma falha | [Troubleshooting](troubleshooting/README.md), [logs](operations/LOGS.md), [integridade de aprovação](operations/REVIEW_INTEGRITY.md) |

## Contratos e decisões

- [Estrutura canônica](contracts/canonical_schema_v4.md) e [fontes acadêmicas](contracts/academic_reference_v4.md).
- [Identificadores e tags](contracts/HI_TAGGING_STANDARD.md).
- [Cobertura funcional e pendências](architecture/FUNCTIONAL_COVERAGE.md).
- [Fontes documentais examinadas](architecture/V4_SOURCE_REVIEW.md).
- [ADRs](adr/README.md): a decisão vigente da jornada é a [ADR 012](adr/012-workbench-academic-v4.md).

## Histórico

[Roteiros V2/V3 arquivados](archive/README.md) servem para interpretar evidências
anteriores. Seus comandos não são instruções para a V4. Os contratos V1 e migrations
antigas continuam versionados para compatibilidade e instalação do banco.
