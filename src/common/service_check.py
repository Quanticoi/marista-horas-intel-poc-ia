"""Dependency checks run inside each provisioned Compose application container."""
import os
import sys
import httpx
from src.persistence.db import rows


def check(service):
    if service == "mlflow":
        rows("SELECT 1", role="mlflow")
    elif service in ("inference", "monitoramento", "dashboard", "model"):
        rows("SELECT 1", role="readonly")
    elif service in ("api", "worker", "ingestion"):
        rows("SELECT 1")
    if service in ("mlflow", "inference", "jupyter", "ingestion", "model"):
        from src.data.storage import s3, bucket
        s3().head_bucket(Bucket=bucket())
    if service in ("inference", "api", "worker", "jupyter", "ingestion", "model"):
        httpx.get(os.environ["MLFLOW_TRACKING_URI"] + "/health", timeout=10).raise_for_status()
    if service in ("api", "worker"):
        from src.workers.tasks import app
        with app.connection_for_write() as connection:
            connection.ensure_connection(max_retries=0)
        httpx.get(os.environ["INFERENCE_URI"] + "/ready", timeout=20).raise_for_status()
    ports = {"mlflow": (5000, "/health"), "inference": (8001, "/ready"),
             "api": (8000, "/ready"), "monitoramento": (8010, "/ready"),
             "dashboard": (8088, "/ready"), "jupyter": (8888, "/login"),
             "ingestion": (8020, "/ready"), "model": (8001, "/ready")}
    if service in ports:
        port, route = ports[service]
        httpx.get(f"http://127.0.0.1:{port}{route}", timeout=25).raise_for_status()
    if service == "worker":
        import socket
        assert app.control.ping(destination=["celery@" + socket.gethostname()], timeout=5)
    if service == "jupyter":
        from src.workbench.journey_config import Settings, sql_engine
        from sqlalchemy import text
        cfg = Settings.load()
        for uri in (cfg.source, cfg.application):
            engine = sql_engine(uri, cfg.timeout)
            try:
                with engine.connect() as connection:
                    assert connection.execute(text("SELECT 1")).scalar_one() == 1
            finally:
                engine.dispose()
        # Imports deliberately exercise dependency compatibility, including SciPy.
        from importlib import import_module
        for dependency in ("statsmodels.api","sklearn","pandas","ipykernel"):
            import_module(dependency)
        assert os.access("/workspace/notebooks", os.W_OK)
    print(f"PASS dependencies: {service}")


if __name__ == "__main__":
    check(sys.argv[1])
