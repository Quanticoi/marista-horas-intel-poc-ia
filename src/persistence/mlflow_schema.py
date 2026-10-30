"""Use the installed MLflow CLI; never reproduce its internal schema."""
import subprocess
from src.common.settings import database_url


def upgrade():
    uri = database_url("mlflow").set(drivername="postgresql+psycopg2").render_as_string(hide_password=False)
    # Capture output: an exception from the database driver can contain credentials.
    result = subprocess.run(["mlflow", "db", "upgrade", uri], capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError("MLflow schema upgrade failed; check PostgreSQL availability and configured MLflow role")
