"""Add immutable draft Planilha Turmas without weakening approved predictions."""
from pathlib import Path
from alembic import op
revision = "004"
down_revision = "003"


def upgrade():
    op.get_bind().connection.driver_connection.execute(
        Path("sql/ddl/004_journey.sql").read_text(encoding="utf-8"), prepare=False)


def downgrade():
    raise RuntimeError("Preserve proposals; restore a verified backup instead")
