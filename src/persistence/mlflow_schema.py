"""Use the installed MLflow CLI; never reproduce its internal schema."""
import subprocess
from sqlalchemy import create_engine, inspect
from src.common.settings import database_url


def upgrade():
    uri = database_url("mlflow").set(drivername="postgresql+psycopg2").render_as_string(hide_password=False)
    engine = create_engine(uri, hide_parameters=True, connect_args={"connect_timeout":10})
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()
    if not tables or tables == {"alembic_version"}:
        # The public SDK initializes a fresh SQL store through MLflow itself.
        # `mlflow db upgrade` alone assumes the initial tracking tables exist.
        initialization = subprocess.run(["python", "-c",
            "import os; from mlflow import MlflowClient; "
            "c=MlflowClient(tracking_uri=os.environ['MLFLOW_INIT_URI'],registry_uri=os.environ['MLFLOW_INIT_URI']); "
            "c.search_experiments(); c.search_registered_models(max_results=1)"],
            env={**__import__('os').environ,"MLFLOW_INIT_URI":uri},capture_output=True,timeout=180)
        if initialization.returncode:
            raise RuntimeError("MLflow fresh SQL store initialization failed; inspect isolated migration diagnostics")
    # Capture output: an exception from the database driver can contain credentials.
    result = subprocess.run(["mlflow", "db", "upgrade", uri], capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError("MLflow schema upgrade failed; check PostgreSQL availability and configured MLflow role")
