"""Explicit draft-only inference in the existing service. No alias or promotion."""
import time
import uuid
import tempfile
from pathlib import Path
from functools import lru_cache
import pandas as pd
import mlflow
import mlflow.sklearn
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from src.common.logging import event
from src.data.journey import FEATURES
from src.common.tracing import operation_span


class DraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    execution_id: uuid.UUID
    model_name: str = Field(pattern=r"^(planilha-turmas-demo|hi\.demo\.[A-Za-z0-9_.-]+)$", max_length=160)
    model_version: str = Field(pattern=r"^[1-9][0-9]*$", max_length=12)
    run_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    snapshot_id: uuid.UUID
    records: list[dict] = Field(min_length=1, max_length=500)
    correlation_id: str | None = Field(default=None,pattern=r"^[a-zA-Z0-9_.-]{1,120}$")
    proposal_id: uuid.UUID | None = None


@lru_cache(maxsize=4)
def load_checked(name,version,expected_sha):
    from src.common.lineage import sha256
    with tempfile.TemporaryDirectory() as directory:
        path=Path(mlflow.artifacts.download_artifacts(artifact_uri=f"models:/{name}/{version}",dst_path=directory))
        if expected_sha and sha256((path/"model.pkl").read_bytes())!=expected_sha:
            raise ValueError("Artifact checksum mismatch")
        return mlflow.sklearn.load_model(str(path))


def load_version(name, version, run_id, execution_id):
    client = mlflow.MlflowClient()
    registered = client.get_model_version(name, version)
    run = client.get_run(run_id)
    if (registered.run_id != run_id or registered.tags.get("execution_id") != execution_id
        or run.data.tags.get("purpose") != "draft-planilha-turmas"
        or run.data.tags.get("mode") != "DEMO" or run.info.status != "FINISHED"):
        raise ValueError("Model is not a finished DEMO version for this execution")
    with operation_span("model.load", model_name=name, model_version=version, run_id=run_id):
        checksum=registered.tags.get("artifact_sha256")
        if name.startswith("hi.demo.") and not checksum:
            raise ValueError("Artifact checksum required")
        model = load_checked(name,version,checksum)
    return model, registered


def router(auth):
    routes = APIRouter()

    @routes.get("/internal/draft/cache",dependencies=[Depends(auth)])
    def cache_status():
        import resource
        return dict(cache=load_checked.cache_info()._asdict(),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                    policy="At most four verified explicit versions per process; registration does not load a model")

    @routes.post("/internal/draft/predict", dependencies=[Depends(auth)])
    def predict(body: DraftRequest):
        start = time.monotonic()
        try:
            fitted, registered = load_version(body.model_name, body.model_version, body.run_id, str(body.execution_id))
            run = mlflow.MlflowClient().get_run(body.run_id)
            if run.data.tags.get("snapshot_id") != str(body.snapshot_id):
                raise ValueError("Snapshot mismatch")
            frame = pd.DataFrame(body.records)
            if set(frame.columns) != set(FEATURES) or frame.isna().any().any():
                raise ValueError("Invalid input schema")
            with operation_span("model.predict", rows=len(frame), model_version=body.model_version):
                values = fitted.predict(frame[FEATURES]).tolist()
            elapsed = time.monotonic()-start
            inference_id = str(uuid.uuid4())
            if mlflow.get_current_active_span() is not None:
                mlflow.update_current_trace(tags={"inference_id":inference_id,"model_key":body.model_name,
                                                  "model_version":body.model_version})
            from src.common.lineage import manifest,put_manifest,utcnow,sha256
            put_manifest(f"lineage/poc/planilha-turmas/inferences/{inference_id}/manifest.json",
                manifest("inference",{},utcnow(),inference_id=inference_id,execution_id=str(body.execution_id),
                    correlation_id=body.correlation_id or str(body.execution_id),proposal_id=str(body.proposal_id) if body.proposal_id else None,
                    snapshot_id=str(body.snapshot_id),run_id=registered.run_id,
                    registered_model_name=body.model_name,model_version=str(registered.version),
                    input_sha256=sha256(body.records),prediction_sha256=sha256(values),row_count=len(values)))
            event("inference", "draft version loaded and predicted", correlation_id=str(body.execution_id),
                run_id=registered.run_id, version=registered.version, rows=len(values), duration_seconds=elapsed)
            return dict(inference_id=inference_id,execution_id=str(body.execution_id), run_id=registered.run_id,
                model_name=body.model_name, model_version=str(registered.version),
                loaded=True, operationally_promoted=False, predictions=values, duration_seconds=elapsed)
        except ValueError:
            raise HTTPException(409, "Version, execution, snapshot or schema mismatch")
        except Exception as error:
            event("inference", "draft inference failed", correlation_id=str(body.execution_id), error=type(error).__name__)
            raise HTTPException(503, "Registered artifact could not be loaded")
    return routes
