from alembic import context
from src.persistence.db import engine

with engine("migration").connect() as connection:
    context.configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()
