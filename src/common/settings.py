import os
from functools import lru_cache
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def config(name):
    return yaml.safe_load((ROOT / "config" / f"{name}.yaml").read_text())


def required(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing configuration: {name}")
    return value


@lru_cache
def database_url(role="app"):
    from sqlalchemy.engine import URL
    users = {"app": ("planning_app", "APP_PASSWORD"),
             "migration": ("planning_migration", "MIGRATION_PASSWORD"),
             "readonly": ("planning_readonly", "READONLY_PASSWORD"),
             "mlflow": ("mlflow", "MLFLOW_PASSWORD"),
             "admin": ("postgres", "POSTGRES_PASSWORD")}
    user, secret = users[role]
    return URL.create("postgresql+psycopg", username=user, password=required(secret),
                      host=os.getenv("DB_HOST", "postgres"),
                      port=int(os.getenv("DB_PORT", "5432")), database=os.getenv("MLFLOW_DB_NAME", "mlflow_db") if role == "mlflow" else
                      "postgres" if role == "admin" else os.getenv("APP_DB_NAME", "planejamento_db"))
