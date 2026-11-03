> Jornada atual (30/10/2026): veja [JOURNEY.md](operations/JOURNEY.md). Notebook principal 01_jornada_completa_planilha_turmas; Docker Compose; eventos atuais no dashboard. Resultados reais e pendencias em history/state.md; validacoes historicas abaixo nao substituem o aceite atual.

# Documentação atual

O ambiente local é Docker Compose. Kubernetes não é requisito para desenvolver.

## Usar o ambiente

- [Fluxo C3: Jupyter, entrada de dados e API por modelo](operations/C3_TRAINING.md).
- [Acessos e credenciais](operations/ACESSOS.md).
- [Subir, parar, reconstruir e validar](commands/DOCKER_COMPOSE.md).
- [Lista de comandos](commands/COMMANDS.md).
- [MLflow: passo a passo da interface](operations/MLFLOW_TUTORIAL.md).
- [RustFS: usuário e senha](operations/RUSTFS.md).
- [Jupyter: editar arquivos locais](operations/JUPYTER.md).
- [Logs](operations/LOGS.md) e [solução de problemas](troubleshooting/README.md).

## Instalar e manter

- [Windows](installation/WINDOWS.md) / [Linux](installation/LINUX.md).
- [PostgreSQL](operations/POSTGRES.md) e [backup/restore](operations/BACKUP_RESTORE.md).
- [Arquitetura](architecture/ARCHITECTURE.md) e [fluxo dos dados](architecture/DATA_FLOW.md).
- [Pendências de aceitação](operations/ACCEPTANCE.md).
- [Limpeza realizada e próximos passos](REPOSITORY_REVIEW.md).

## Referências preservadas

- [Decisões arquiteturais](adr/README.md): histórico identificado; ADRs 007/008 definem o fluxo atual.

A estrutura atual distribui somente a Jornada Completa. Consulte a revisão do repositório para a lista de itens removidos e os dados preservados.