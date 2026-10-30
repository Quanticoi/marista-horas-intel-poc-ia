"""Load approved fitted binaries; never train during inference."""
from functools import lru_cache
import pandas as pd
from mlflow import MlflowClient
from src.mlops.artifacts import load_bundle
from src.persistence.db import rows
from src.inference.contracts import InferenceResponse


@lru_cache(maxsize=2)
def artifact(uri, version, checksum):
    return load_bundle(uri, checksum)


def approved(deployment_id, model_key):
    deployments = rows("""SELECT d.*,m.model_key FROM planning.model_deployments d
        JOIN planning.model_catalog m ON m.id=d.model_id
        WHERE d.id=:id AND d.status='APPROVED' AND d.alias='champion' AND m.active""",
        {"id":deployment_id}, role="readonly")
    if not deployments or deployments[0]["model_key"] != model_key:
        raise ValueError("Approved deployment not found")
    deployment = deployments[0]
    alias = MlflowClient().get_model_version_by_alias(model_key, "champion")
    if str(alias.version) != deployment["registered_version"] or alias.source != deployment["artifact_uri"]:
        raise ValueError("Registry inconsistency; reconciliation required")
    if not deployment.get("artifact_sha256") or deployment["artifact_sha256"] != alias.tags.get("bundle_sha256") or deployment["mlflow_run_id"] != alias.run_id:
        raise ValueError("Approved binary provenance changed")
    return deployment, alias


def infer(request):
    deployment, alias = approved(request.deployment_id, request.model_key)
    model, info = artifact(deployment["artifact_uri"], deployment["registered_version"], deployment["artifact_sha256"])
    if info["model_key"] != request.model_key or info["snapshot_id"] != str(request.snapshot_id) or info["run_id"] != alias.run_id:
        raise ValueError("Model/snapshot/run provenance mismatch")
    if info["code_version"] != deployment["code_version"] or info["dataset_sha256"] != deployment["dataset_sha256"]:
        raise ValueError("Approved code/dataset provenance mismatch")
    frame = pd.DataFrame({"target_year":[request.target_year], "target_semester":[request.target_semester]})
    value = float(model.predict(frame)[0])
    return InferenceResponse(deployment_id=request.deployment_id, snapshot_id=request.snapshot_id,
        model_key=request.model_key, registered_version=deployment["registered_version"],
        forecast_raw=value, is_fallback=info["fallback"], mlflow_run_id=info["run_id"],
        code_version=info["code_version"], dataset_sha256=info["dataset_sha256"])
