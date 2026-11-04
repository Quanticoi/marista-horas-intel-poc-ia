from pathlib import Path
from alembic import op
revision="006"
down_revision="005"

def upgrade():
    op.get_bind().connection.driver_connection.execute(Path("sql/ddl/006_operations.sql").read_text(encoding="utf-8"),prepare=False)

def downgrade():
    raise RuntimeError("Preserve operational history; destructive downgrade unsupported")
