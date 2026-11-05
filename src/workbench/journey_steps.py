"""Bounded checks and observable notebook steps. No local tracking fallback."""
import os
import time
import tempfile
from pathlib import Path
from contextlib import contextmanager
import httpx
import mlflow
from sqlalchemy import text
from src.common.logging import event
from src.workbench.journey_config import sql_engine
from src.common.tracing import stage_span


@contextmanager
def step(name, execution_id, statuses):
    start = time.monotonic()
    attempt = 1 + sum(row["stage"] == name for row in statuses)
    trace_info = {"attempt": attempt}
    event("journey", "stage started", stage=name, correlation_id=execution_id)
    try:
        with stage_span(name, execution_id, attempt) as span:
            if span is not None:
                trace_info["trace_id"] = span.trace_id
            yield
    except Exception as error:
        missing = getattr(error, "name", None) if isinstance(error, NameError) else None
        missing = missing if isinstance(missing, str) and missing.isidentifier() and len(missing) < 100 else None
        detail = f" Nome não definido: {missing}. Execute as etapas anteriores na ordem." if missing else ""
        statuses.append(dict(stage=name, status="FAILED", seconds=round(time.monotonic()-start, 3), **trace_info))
        event("journey", "stage failed", stage=name, correlation_id=execution_id,
              error=type(error).__name__, missing_name=missing, level="ERROR")
        if mlflow.active_run():
            try:
                mlflow.set_tag("failure_stage", name)
                mlflow.end_run(status="FAILED")
            except Exception:
                # An unavailable tracking server must not hide the original failure.
                event("journey", "tracking failure could not be persisted", stage=name,
                      correlation_id=execution_id, level="ERROR")
        raise RuntimeError(f"Etapa {name} falhou ({type(error).__name__}).{detail} Consulte os eventos por correlation_id={execution_id}; docker compose logs --tail 100 mlflow api inference") from None
    else:
        duration = round(time.monotonic()-start, 3)
        statuses.append(dict(stage=name, status="PASS", seconds=duration, **trace_info))
        event("journey", "stage completed", stage=name, correlation_id=execution_id, duration_seconds=duration, **trace_info)


def dependencies(cfg, execution_id, diagnostic_experiment='journey-diagnostics-proxy'):
    os.environ["MLFLOW_HTTP_REQUEST_TIMEOUT"] = str(cfg.timeout)
    os.environ["MLFLOW_HTTP_REQUEST_MAX_RETRIES"] = str(cfg.retries)
    mlflow.set_tracking_uri(cfg.tracking)
    mlflow.set_registry_uri(cfg.tracking)
    result = []

    def sql_check(url):
        engine = sql_engine(url, cfg.timeout)
        try:
            with engine.connect() as con:
                assert con.execute(text("SELECT 1")).scalar_one() == 1
        finally:
            engine.dispose()

    def tracking_check():
        httpx.get(cfg.tracking + "/health", timeout=cfg.timeout).raise_for_status()
        server = httpx.get(cfg.tracking + "/version", timeout=cfg.timeout)
        server.raise_for_status()
        if server.text.strip('"\n ') != mlflow.__version__:
            raise ValueError("MLflow server and SDK version mismatch")
        client = mlflow.MlflowClient()
        name = diagnostic_experiment
        experiment = client.get_experiment_by_name(name)
        eid = experiment.experiment_id if experiment else client.create_experiment(name)
        with mlflow.start_run(experiment_id=eid, tags={"purpose":"dependency-diagnostic", "execution_id":execution_id}) as run:
            if not run.info.artifact_uri.startswith("mlflow-artifacts:"):
                raise ValueError("Diagnostic experiment does not use artifact proxy")
            mlflow.log_param("check", "write-read")
            with tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / "diagnostic.txt"
                path.write_text(execution_id)
                mlflow.log_artifact(str(path))
                downloaded = client.download_artifacts(run.info.run_id, "diagnostic.txt", folder + "/download")
                assert Path(downloaded).read_text() == execution_id
            assert client.get_run(run.info.run_id).data.params["check"] == "write-read"

    checks = [("source SQL", lambda: sql_check(cfg.source)),
              ("application SQL", lambda: sql_check(cfg.application)),
              ("MLflow PostgreSQL + proxy artifact roundtrip", tracking_check)]
    for name, check in checks:
        for attempt in range(cfg.retries + 1):
            try:
                check()
                result.append({"dependency": name, "status": "PASS", "attempts": attempt + 1})
                break
            except Exception as error:
                if attempt == cfg.retries:
                    result.append({"dependency": name, "status": "FAIL", "error": type(error).__name__})
                else:
                    time.sleep(1)
    return result


def require_dependencies(status, cfg):
    if any(row["status"] != "PASS" for row in status):
        raise RuntimeError(f"Dependências indisponíveis; treino bloqueado. MLflow: {cfg.tracking}. Execute docker compose logs --tail 100 mlflow postgres rustfs. Nenhum tracking local foi iniciado.")
