from pathlib import Path
from alembic import op

revision='009'
down_revision='008'

def upgrade():
    op.get_bind().connection.driver_connection.execute(
        Path('sql/ddl/009_review_integrity.sql').read_text(encoding='utf-8'),
        prepare=False)

def downgrade():
    raise RuntimeError('Approval checkpoints and immutable lineage cannot be safely downgraded')
