> **Registro de decisão anterior.** A jornada V4 é regida pela [ADR 012](012-workbench-academic-v4.md). Topologias, comandos ou responsabilidades deste registro podem ter sido substituídos; use a [documentação operacional atual](../README.md).

# ADR 008 — Fluxo C3 e servidor por modelo

Status: implementado para Compose; provisionamento final e homologação pendentes.
Data: 2026-10-28. Solicitação: treinamento no Jupyter/SDK, PostgreSQL exclusivo,
binários no RustFS e uma API por modelo, com serviço específico de entrada.

Decisões:
- Workbench usa HTTP para Tracking/Registry e serviço de entrada; não abre conexão SQL.
- Uma instância PostgreSQL, bancos planejamento_db e mlflow_db separados; nenhum SQLite.
- Upload direto S3, bundles ajustados com manifest de integridade; sem fit durante previsão.
- Aprovação auditada congela versão, run e hashes no PostgreSQL; publicação é explícita.
- API/container por modelo, versão fixada por implantação; roteador preserva a API de negócio.
- Atualização falha de forma fechada até republicação. Rollout sem interrupção não implementado.
- Recursos de teste isolados são descartáveis; dados existentes e notebooks locais preservados.

Substitui o formato JSON de inferência da baseline anterior. Helm permanece histórico e
não representa esta implantação atualizada. GCP exige implementação própria de rede,
autenticação/TLS, GCS, identidade e Artifact Registry.

[Operação](../operations/C3_TRAINING.md).
