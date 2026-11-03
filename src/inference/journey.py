"""Explicit draft-only inference in the existing service. No alias or promotion."""
import time
import uuid
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
    model_name: str = Field(pattern=r"^planilha-turmas-demo$", max_length=100)
    model_version: str = Field(pattern=r"^[1-9][0-9]*$", max_length=12)
    run_id: str = Field(pattern=r"^[a-f0-9]{32}$")
    snapshot_id: uuid.UUID
    records: list[dict] = Field(min_length=1, max_length=500)


def load_version(name, version, run_id, execution_id):
    client = mlflow.MlflowClient()
    registered = client.get_model_version(name, version)
    run = client.get_run(run_id)
    if (registered.run_id != run_id or registered.tags.get("execution_id") != execution_id
        or run.data.tags.get("purpose") != "draft-planilha-turmas"
        or run.data.tags.get("mode") != "DEMO" or run.info.status != "FINISHED"):
        raise ValueError("Model is not a finished DEMO version for this execution")
    with operation_span("model.load", model_name=name, model_version=version, run_id=run_id):
        model = mlflow.sklearn.load_model(f"models:/{name}/{version}")
    return model, registered


def router(auth):
    routes = APIRouter()

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
            event("inference", "draft version loaded and predicted", correlation_id=str(body.execution_id),
                run_id=registered.run_id, version=registered.version, rows=len(values), duration_seconds=elapsed)
            return dict(execution_id=str(body.execution_id), run_id=registered.run_id,
                model_name=body.model_name, model_version=str(registered.version),
                loaded=True, operationally_promoted=False, predictions=values, duration_seconds=elapsed)
        except ValueError:
            raise HTTPException(409, "Version, execution, snapshot or schema mismatch")
        except Exception as error:
            event("inference", "draft inference failed", correlation_id=str(body.execution_id), error=type(error).__name__)
            raise HTTPException(503, "Registered artifact could not be loaded")
    return routes
