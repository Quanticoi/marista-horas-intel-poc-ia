from pathlib import Path
from alembic import op
revision='013'
down_revision='012'

def upgrade():
    op.get_bind().connection.driver_connection.execute(Path('sql/ddl/013_workbench_campaigns.sql').read_text(encoding='utf-8'),prepare=False)

def downgrade():
    raise RuntimeError('Scientific checkpoints must be preserved')
