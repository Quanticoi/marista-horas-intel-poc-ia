from pathlib import Path
from alembic import op

revision = '010'
down_revision = '009'


def upgrade():
    op.get_bind().connection.driver_connection.execute(
        Path('sql/ddl/010_academic_reference.sql').read_text(encoding='utf-8'), prepare=False)


def downgrade():
    raise RuntimeError('Academic source provenance is append-only; destructive downgrade forbidden')
