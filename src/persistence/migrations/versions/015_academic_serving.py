from pathlib import Path
from alembic import op
revision='015'
down_revision='014'

def upgrade():
    op.get_bind().connection.driver_connection.execute(Path('sql/ddl/015_academic_serving.sql').read_text(encoding='utf-8'),prepare=False)

def downgrade():
    raise RuntimeError('Academic serving and proposal history cannot be removed')
