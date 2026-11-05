> **Registro de decisão anterior.** A jornada V4 é regida pela [ADR 012](012-workbench-academic-v4.md). Topologias, comandos ou responsabilidades deste registro podem ter sido substituídos; use a [documentação operacional atual](../README.md).

# ADR-005 — Ambiente local e evidência de entrega

**Registro histórico.** Contexto Rancher, Secrets e purge abaixo descrevem o ambiente
anterior, substituído pela [ADR 007](007-compose-development.md). O build e a migração
Compose foram validados em 26/10/2026; os bloqueios iniciais não são o status atual
dos serviços. Credenciais/acessos atuais: [ACESSOS.md](../operations/ACESSOS.md).

Contexto obrigatório rancher-desktop, acesso HTTP por loopback; tokens locais em
Secrets, API sem superuser e dashboard readonly. Deploy não instala Python no host.
Purge exige texto digitado, não apaga namespaces arbitrários e só remove PVCs rotulados.
Restore cria novas bases e nunca sobrescreve existentes.

MLflow candidato 3.11.1: revisão inicial identificou incompatibilidade entre MLflow
2.20.2 (pyarrow<19) e pyarrow 19. A baseline foi atualizada antes do build; dependências
diretas são fixadas, mas o resolver e a integração ainda precisam ser executados.
Não foi gerado lock transitive fictício. Fonte de metadados: https://pypi.org/project/mlflow/3.11.1/

Fluxo development → staging validada → main homologada. Ambiente de autoria bloqueou
escrita Git/rede e execução de winget; não contornar isolamento ou apagar história.
Evidências negativas também são registradas em history e artifacts/reports.
