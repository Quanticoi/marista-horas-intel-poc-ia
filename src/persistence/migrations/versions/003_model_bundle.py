"""Pin approved binary provenance independently of mutable Registry tags."""
from alembic import op

revision = "003"
down_revision = "002"


def upgrade():
    for column, kind in [("mlflow_run_id", "varchar(100)"), ("code_version", "varchar(80)"),
                         ("dataset_sha256", "char(64)"), ("artifact_sha256", "char(64)")]:
        op.execute(f"ALTER TABLE planning.model_deployments ADD COLUMN IF NOT EXISTS {column} {kind}")


def downgrade():
    raise RuntimeError("Do not remove approved model provenance")
