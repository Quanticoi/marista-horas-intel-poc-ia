"""Run after the notebook. Real SQL, Registry, artifact proxy and application HTTP."""
import json
import os
import uuid
from dataclasses import replace
from pathlib import Path
import httpx
import mlflow
import pytest
from sqlalchemy import text
from src.workbench.journey_config import Settings, sql_engine
from src.workbench.journey_steps import dependencies, require_dependencies
from src.data.journey import extract, prepare, FEATURES
from src.inference.journey import load_version
from src.persistence.journey import compose, persist
from src.common.settings import required

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def restore_tracking_configuration():
    # MLflow setters also change environment variables; failure injection must
    # restore both SDK state and environment before the next test loads Settings.
    names = ("MLFLOW_TRACKING_URI", "MLFLOW_REGISTRY_URI",
             "MLFLOW_HTTP_REQUEST_TIMEOUT", "MLFLOW_HTTP_REQUEST_MAX_RETRIES")
    original = {name: os.environ.get(name) for name in names}
    tracking, registry = mlflow.get_tracking_uri(), mlflow.get_registry_uri()
    try:
        yield
    finally:
        mlflow.set_tracking_uri(tracking)
        mlflow.set_registry_uri(registry)
        for name, value in original.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def context():
    cfg = Settings.load()
    report = json.loads(Path("/reports/journey-latest.json").read_text())
    mlflow.set_tracking_uri(cfg.tracking)
    mlflow.set_registry_uri(cfg.tracking)
    frame, snapshot = extract(cfg)
    _, _, future = prepare(frame, snapshot)
    restored, _ = load_version(report["model_name"],report["model_version"],report["run_id"],report["execution_id"])
    lines = compose(future, restored.predict(future[FEATURES]))
    return cfg, report, snapshot, future, lines


def test_persisted_version_api_and_idempotency():
    cfg, report, snapshot, future, lines = context()
    first = persist(cfg,report["execution_id"],snapshot,report,lines)
    second = persist(cfg,report["execution_id"],snapshot,report,lines)
    assert first == second
    headers = {"Authorization":"Bearer "+required("API_TOKEN")}
    response = httpx.get(cfg.api+f"/v1/proposals/{report['execution_id']}/lines?limit=500",headers=headers,timeout=15)
    response.raise_for_status()
    assert len(response.json()) == len(lines) == report["persisted_rows"]
    altered = [dict(row) for row in lines]
    altered[0]["proposed_students"] += 1
    with pytest.raises(ValueError,match="different payload"):
        persist(cfg,report["execution_id"],snapshot,report,altered)


def test_atomic_rollback_on_invalid_discipline():
    cfg, report, snapshot, _, lines = context()
    execution = str(uuid.uuid4())
    lines[-1]["discipline_id"] = str(uuid.uuid4())
    with pytest.raises(Exception):
        persist(cfg,execution,snapshot,report,lines)
    engine = sql_engine(cfg.application)
    try:
        with engine.connect() as con:
            assert con.execute(text("SELECT count(*) FROM planning.proposal_generations WHERE execution_id=:id"), {"id":execution}).scalar_one() == 0
    finally:
        engine.dispose()


def test_unavailable_mlflow_fails_before_fit(tmp_path, monkeypatch):
    # Closed loopback port inside the test container: no shared service is stopped.
    from sklearn.linear_model import Ridge
    monkeypatch.setattr(Ridge,"fit",lambda *a,**k:pytest.fail("Fit must not run"))
    cfg = replace(Settings.load(), tracking="http://127.0.0.1:1", timeout=1, retries=0)
    monkeypatch.chdir(tmp_path)
    checks = dependencies(cfg,str(uuid.uuid4()))
    assert checks[-1]["status"] == "FAIL"
    with pytest.raises(RuntimeError,match="treino bloqueado"):
        require_dependencies(checks,cfg)
    assert not (tmp_path/"mlruns").exists()
    assert not (tmp_path/"mlflow.db").exists()


def test_service_rejects_wrong_version_identity():
    cfg, report, snapshot, future, _ = context()
    body = dict(execution_id=str(uuid.uuid4()), snapshot_id=snapshot["id"],
        model_name=report["model_name"],model_version=report["model_version"],run_id=report["run_id"],
        records=future[FEATURES].to_dict("records"))
    response = httpx.post(cfg.inference+"/internal/draft/predict",json=body,
        headers={"Authorization":"Bearer "+required("INFERENCE_TOKEN")},timeout=30)
    assert response.status_code == 409


def test_draft_api_auth_and_filters():
    cfg, report, _, _, _ = context()
    assert httpx.get(cfg.api+f"/v1/proposals/{report['execution_id']}",timeout=15).status_code == 401
    headers={"Authorization":"Bearer "+required("API_TOKEN")}
    assert httpx.get(cfg.api+f"/v1/proposals/{uuid.uuid4()}",headers=headers,timeout=15).status_code == 404
    result=httpx.get(cfg.api+"/v1/proposals",params={"cycle":cfg.cycle,"limit":500},headers=headers,timeout=15)
    result.raise_for_status()
    assert any(r["execution_id"]==report["execution_id"] for r in result.json())


def test_model_bytes_in_object_store_match_proxy(tmp_path):
    """Read-only proof: persisted bytes in RustFS equal the registered model download."""
    import hashlib
    from src.data.storage import s3, bucket
    cfg, report, _, _, _ = context()
    client = mlflow.MlflowClient()
    version = client.get_model_version(report["model_name"], report["model_version"])
    assert version.run_id == report["run_id"]
    logged = client.get_logged_model(version.source.removeprefix("models:/"))
    assert logged.artifact_location.startswith("mlflow-artifacts:/")
    location = logged.artifact_location.removeprefix("mlflow-artifacts:/").lstrip("/")
    response = s3().get_object(Bucket=bucket(), Key=f"mlflow/{location}/model.pkl")
    try:
        stored = response["Body"].read()
    finally:
        response["Body"].close()
    downloaded = mlflow.artifacts.download_artifacts(
        artifact_uri=report["model_uri"], dst_path=str(tmp_path))
    assert hashlib.sha256(stored).digest() == hashlib.sha256(
        (Path(downloaded) / "model.pkl").read_bytes()).digest()
    run = client.get_run(report["run_id"])
    assert run.data.params["algorithm"] == "Ridge"
    assert run.data.metrics["mae"] == report["metrics"]["mae"]
    assert run.data.tags["execution_id"] == report["execution_id"]


def test_dashboard_has_correlated_journey_events():
    _, report, _, _, _ = context()
    response = httpx.get(required("DASHBOARD_URI") + "/api/logs",
        params={"correlation_id": report["execution_id"], "limit": 100},
        headers={"Authorization": "Bearer " + required("DASHBOARD_TOKEN")}, timeout=15)
    response.raise_for_status()
    services = {row["service"] for row in response.json()}
    assert {"journey", "inference", "api"} <= services


def test_traces_persisted_with_remote_spans_and_no_payloads():
    report = json.loads(Path("/reports/journey-latest.json").read_text())
    assert report["traces"]
    all_names = set()
    for item in report["traces"]:
        recorded = mlflow.get_trace(item["trace_id"])
        assert recorded.info.tags["execution_id"] == report["execution_id"]
        assert recorded.info.tags["run_id"] == report["run_id"]
        for span in recorded.data.spans:
            all_names.add(span.name)
            assert span.inputs is None and span.outputs is None
    assert {"inference.http", "api.http", "postgres.query", "model.load", "model.predict"} <= all_names


def test_read_only_storage_and_business_database_evidence():
    from src.workbench.verification import verify_model_storage, verify_proposal_sql
    cfg, report, _, _, lines = context()
    storage = verify_model_storage(report)
    assert len(storage) == 3 and all(row["status"] == "PASS" for row in storage)
    evidence = verify_proposal_sql(cfg, report["execution_id"], report, lines)
    assert evidence["status"] == "PASS" and evidence["stored_rows"] == report["persisted_rows"]
    altered = [dict(r) for r in lines]
    altered[0]["proposed_students"] += 1
    with pytest.raises(ValueError, match="differs"):
        verify_proposal_sql(cfg, report["execution_id"], report, altered)


def test_repeated_stage_records_distinct_attempts_and_safe_failure():
    from src.common import tracing
    from src.workbench.journey_steps import step
    cfg = Settings.load()
    cfg.experiment = 'HI/POC/Diagnostics/Regression'
    original = tracing._experiment_id
    statuses = []
    execution = str(uuid.uuid4())
    try:
        tracing.configure_tracing(cfg)
        with step("diagnostic repeated stage", execution, statuses):
            pass
        with pytest.raises(RuntimeError, match="Nome não definido: model"):
            with step("diagnostic repeated stage", execution, statuses):
                raise NameError("password=do-not-export", name="model")
        assert [r["attempt"] for r in statuses] == [1, 2]
        assert statuses[0]["trace_id"] != statuses[1]["trace_id"]
        for status in statuses:
            mlflow.MlflowClient().set_trace_tag(status["trace_id"], "purpose", "controlled-failure-test")
        failed = mlflow.get_trace(statuses[1]["trace_id"])
        assert str(failed.info.state) == "ERROR"
        assert "do-not-export" not in json.dumps(failed.to_dict(), default=str)
    finally:
        tracing._experiment_id = original
