from pathlib import Path
from alembic import op
revision='014'
down_revision='013'


def upgrade():
    op.get_bind().connection.driver_connection.execute(Path('sql/ddl/014_academic_dimensions.sql').read_text(encoding='utf-8'),prepare=False)


def downgrade():
    raise RuntimeError('Canonical reference read models are retained for audit')
