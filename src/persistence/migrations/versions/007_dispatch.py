from pathlib import Path
from alembic import op
revision="007"
down_revision="006"
def upgrade():
    op.get_bind().connection.driver_connection.execute(Path("sql/ddl/007_dispatch.sql").read_text(),prepare=False)
def downgrade():
    raise RuntimeError("Preserve operation state")
