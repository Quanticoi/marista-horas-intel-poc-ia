from pathlib import Path
from alembic import op
revision='008'
down_revision='007'

def upgrade():
    op.get_bind().connection.driver_connection.execute(Path('sql/ddl/008_tagging_catalog.sql').read_text(encoding='utf-8'),prepare=False)

def downgrade():
    raise RuntimeError('Preserve immutable catalog history')
