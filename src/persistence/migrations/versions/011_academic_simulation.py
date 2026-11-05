from pathlib import Path
from alembic import op
revision='011'
down_revision='010'

def upgrade():
    op.get_bind().connection.driver_connection.execute(Path('sql/ddl/011_academic_simulation.sql').read_text(encoding='utf-8'),prepare=False)

def downgrade():
    raise RuntimeError('Immutable synthetic snapshots cannot be downgraded destructively')
