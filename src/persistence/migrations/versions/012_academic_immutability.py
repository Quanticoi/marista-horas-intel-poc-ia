from pathlib import Path
from alembic import op
revision='012'
down_revision='011'


def upgrade():
    op.get_bind().connection.driver_connection.execute(Path('sql/ddl/012_academic_immutability.sql').read_text(encoding='utf-8'),prepare=False)


def downgrade():
    raise RuntimeError('Do not remove provenance immutability protections')
