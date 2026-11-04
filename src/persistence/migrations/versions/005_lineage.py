"""Add immutable lineage and application contract evidence; retain all legacy IDs."""
from pathlib import Path
from alembic import op
revision = "005"
down_revision = "004"


def upgrade():
    op.get_bind().connection.driver_connection.execute(
        Path("sql/ddl/005_lineage.sql").read_text(encoding="utf-8"), prepare=False)


def downgrade():
    raise RuntimeError("Append-only evidence must be preserved")
