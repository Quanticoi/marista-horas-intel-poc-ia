"""Canonical DDL, extracted without changing fields or constraints."""
from pathlib import Path
from alembic import op

revision = "001"
down_revision = None


def upgrade():
    sql = Path("sql/ddl/001_planning.sql").read_text(encoding="utf-8")
    op.get_bind().connection.driver_connection.execute(sql, prepare=False)


def downgrade():
    raise RuntimeError("Destructive downgrade prohibited; restore a verified backup")
