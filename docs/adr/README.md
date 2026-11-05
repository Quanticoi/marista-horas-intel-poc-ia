# Decisões arquiteturais

A [ADR 012 — Workbench e inferência V4](012-workbench-academic-v4.md) rege a jornada
atual. A [ADR 007](007-compose-development.md) registra a adoção do Docker Compose.
Os documentos abaixo preservam a evolução; não são roteiros de instalação atuais.

| Registro | Tema | Situação na V4 |
|---|---|---|
| [001](001-rustfs.md) | RustFS | Produto mantido; implantação original substituída |
| [002](002-schema.md) | DDL e imutabilidade | Base preservada e migrations aditivas |
| [003](003-logs-pvc.md) | Logs e PVC | Topologia histórica |
| [004](004-workbench.md) | Treinamento local | Execução atual definida na 012 |
| [005](005-security-delivery.md) | Ambiente inicial | Registro histórico |
| [006](006-inference-monitoring-pods.md) | Inferência/monitoramento | Separação funcional mantida; runtime atualizado |
| [007](007-compose-development.md) | Compose | Runtime mantido; migração histórica concluída |
| [008](008-c3-binary-serving.md) | API por modelo e upload direto | Fluxo legado; V4 usa serving compartilhado e proxy |
| [009](009-lineage-contract.md) | Contrato V1 | Compatibilidade; V4 entrega contrato HTTP v2 |
| [010](010-durable-operations-v2.md) | Jobs e governança | Geração recuperável mantida; treinamento no worker desativado |
| [012](012-workbench-academic-v4.md) | V4 | Vigente, com experimento por campanha e reset seletivo |
