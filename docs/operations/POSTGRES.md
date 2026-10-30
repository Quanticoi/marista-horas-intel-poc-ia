# PostgreSQL

postgres:15.10-bookworm com volume nomeado, sem porta pública no host.
Bootstrap cria planejamento_db/mlflow_db e papéis separados. Preserve .env.
Alembic aplica revisões; não execute DDL duplicada. Auditoria append-only e
snapshots/previsões protegidos por triggers. Aplicação psycopg3; MLflow psycopg2.

Consultas em sql/queries/operations.sql. Console:
`docker compose exec postgres psql -U postgres -d planejamento_db`.
Produção exige TLS, acesso institucional, HA e backup externo.
