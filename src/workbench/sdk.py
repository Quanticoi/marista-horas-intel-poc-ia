"""Notebook SDK: HTTP to MLflow/intake; S3 to RustFS; never direct SQL."""
import hashlib
from urllib.parse import urlparse
import httpx
import mlflow
from src.common.settings import required, ROOT
from src.data.storage import s3, bucket


def source_version():
    # Content identity works even before a repository has a Git commit.
    sha = hashlib.sha256()
    for path in sorted((ROOT / "src").rglob("*.py")):
        sha.update(path.relative_to(ROOT).as_posix().encode())
        sha.update(path.read_bytes())
    for path in [ROOT / "pyproject.toml", ROOT / "config/training.yaml"]:
        sha.update(path.read_bytes())
    return "sha256:" + sha.hexdigest()


def connect():
    for key in ("MLFLOW_TRACKING_URI", "INGESTION_URI"):
        uri = urlparse(required(key))
        if uri.scheme not in ("http", "https") or not uri.netloc or uri.username or uri.password:
            raise ValueError(f"{key} must point to a remote HTTP(S) service")
    mlflow.set_tracking_uri(required("MLFLOW_TRACKING_URI"))
    mlflow.set_registry_uri(required("MLFLOW_TRACKING_URI"))
    httpx.get(required("MLFLOW_TRACKING_URI") + "/health", timeout=10).raise_for_status()
    httpx.get(required("INGESTION_URI") + "/ready", timeout=15).raise_for_status()
    s3().head_bucket(Bucket=bucket())
    return {"tracking":"remote", "registry":"same server", "database":"PostgreSQL via services", "storage":"S3/RustFS"}


def intake(method, path, body=None):
    response = httpx.request(method, required("INGESTION_URI") + path, json=body,
        headers={"Authorization":"Bearer " + required("INGESTION_TOKEN")}, timeout=120)
    if response.status_code >= 400:
        raise RuntimeError(f"Intake request failed: HTTP {response.status_code}; check intake logs")
    return response.json()


def submit_dataset(payload):
    from src.ingestion.contracts import Dataset
    validated = Dataset.model_validate(payload)
    return intake("POST", "/v1/datasets", validated.model_dump(mode="json"))


def test_dataset():
    from src.data.synthetic import generate
    return dict(source="SYNTHETIC-C3", as_of_date="2025-12-31", target_year=2026,
                target_semester=1, records=generate())


def train(snapshot_id, model_key=None):
    connect()
    from src.training.pipeline import train as execute
    return execute(snapshot_id, model_key=model_key)
