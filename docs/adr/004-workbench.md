> **Registro de decisão anterior.** A jornada V4 é regida pela [ADR 012](012-workbench-academic-v4.md). Topologias, comandos ou responsabilidades deste registro podem ter sido substituídos; use a [documentação operacional atual](../README.md).

# ADR-004 — Treino local supervisionado

**Histórico de implantação:** namespaces/Jobs locais foram substituídos pela
[ADR 007](007-compose-development.md). Permanecem válidos o treinamento explícito
e a aprovação humana. Hoje o Jupyter usa workspace local e o treino usa tools no Compose.

Jupyter no namespace training simula Workbench; código comum fica em src. Treino via
Job explícito, serial na baseline, com métricas de recurso. Notebooks não executam
treino/promoção automaticamente. GKE, Azure/Entra/Apigee e dados institucionais são
fora de escopo; nenhum resultado local serve como comprovação dessas integrações.
