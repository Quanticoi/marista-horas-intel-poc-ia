"""Seal snapshots/history and preserve original predictions; ADR-002."""
from pathlib import Path
from alembic import op

revision = "002"
down_revision = "001"


def upgrade():
    op.get_bind().connection.driver_connection.execute(
        Path("sql/ddl/002_immutability.sql").read_text(encoding="utf-8"),prepare=False)


def downgrade():
    raise RuntimeError("Downgrade would remove provenance protection")
