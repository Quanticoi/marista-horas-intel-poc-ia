"""Read-only evidence from Object Store and business PostgreSQL, not MLflow tables."""
import hashlib
import tempfile
from pathlib import Path

import mlflow
from sqlalchemy import text
from src.common.settings import ROOT
from src.data.journey import KEYS
from src.data.storage import s3, bucket
from src.workbench.journey_config import sql_engine


def verify_model_storage(trace):
    client = mlflow.MlflowClient()
    version = client.get_model_version(trace["model_name"], trace["model_version"])
    if version.run_id != trace["run_id"]:
        raise ValueError("Registered version does not belong to this run")
    logged = client.get_logged_model(version.source.removeprefix("models:/"))
    if not logged.artifact_location.startswith("mlflow-artifacts:/"):
        raise ValueError("Expected proxy artifact location")
    prefix = "mlflow/" + logged.artifact_location.removeprefix("mlflow-artifacts:/").lstrip("/")
    storage = s3()
    evidence = []
    with tempfile.TemporaryDirectory() as folder:
        downloaded = Path(mlflow.artifacts.download_artifacts(artifact_uri=trace["model_uri"], dst_path=folder))
        for filename in ("MLmodel", "model.pkl", "requirements.txt"):
            key = f"{prefix}/{filename}"
            response = storage.get_object(Bucket=bucket(), Key=key)
            try:
                stored = response["Body"].read()
            finally:
                response["Body"].close()
            digest = hashlib.sha256(stored).hexdigest()
            if digest != hashlib.sha256((downloaded / filename).read_bytes()).hexdigest():
                raise ValueError(f"Storage and proxy bytes differ: {filename}")
            evidence.append(dict(bucket=bucket(), key=key, bytes=len(stored), sha256=digest,
                                 model_version=str(version.version), status="PASS"))
    return evidence


def verify_proposal_sql(cfg, execution_id, trace, expected_lines):
    query = ROOT / "sql/queries/verify_proposal.sql"
    engine = sql_engine(cfg.application, cfg.timeout)
    try:
        # New connection after persist() has committed its transaction.
        with engine.connect() as con:
            summary = dict(con.execute(text(query.read_text()), {"execution_id": execution_id}).mappings().one())
            stored = con.execute(text("SELECT * FROM planning.proposal_lines WHERE execution_id=:execution_id"),
                                 {"execution_id": execution_id}).mappings().all()
    finally:
        engine.dispose()
    if (summary["run_id"] != trace["run_id"] or summary["model_name"] != trace["model_name"]
            or summary["model_version"] != trace["model_version"]
            or int(summary["row_count"]) != len(expected_lines) or len(stored) != len(expected_lines)):
        raise ValueError("Persisted proposal identity/count mismatch")
    expected = {tuple(str(r[k]) for k in KEYS): r for r in expected_lines}
    for row in stored:
        original = expected[tuple(str(row[k]) for k in KEYS)]
        for key in ("forecast_raw", "proposed_students", "proposed_groups", "human_adjustment"):
            if row[key] != original[key]:
                raise ValueError(f"Persisted proposal differs: {key}")
    return dict(database="planejamento_db", schema="planning", status="PASS",
                execution_id=str(summary["execution_id"]), run_id=summary["run_id"],
                model_version=summary["model_version"], proposal_status=summary["status"],
                stored_rows=int(summary["stored_rows"]), proposed_students=int(summary["proposed_students"]),
                proposed_groups=int(summary["proposed_groups"]), query=str(query.relative_to(ROOT)))
