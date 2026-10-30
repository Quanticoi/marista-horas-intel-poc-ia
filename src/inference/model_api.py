"""Dedicated server, pinned to exactly one approved model deployment."""
from contextlib import asynccontextmanager
from uuid import UUID
from fastapi import FastAPI, Depends, HTTPException
from src.common.settings import required
from src.common.http_limits import BodyLimitMiddleware
from src.inference.main import auth
from src.inference.contracts import InferenceRequest, InferenceResponse
from src.inference.runtime import approved, artifact, infer


def identity():
    return required("MODEL_KEY"), required("REGISTERED_VERSION"), UUID(required("MODEL_DEPLOYMENT_ID"))


def warmup():
    key, version, deployment = identity()
    row, registered = approved(deployment, key)
    if row["registered_version"] != version:
        raise ValueError("Published version is no longer approved")
    _, info = artifact(row["artifact_uri"], version, row["artifact_sha256"])
    if info["model_key"] != key or info["run_id"] != registered.run_id or info["code_version"] != row["code_version"] or info["dataset_sha256"] != row["dataset_sha256"]:
        raise ValueError("Published binary provenance mismatch")


@asynccontextmanager
async def lifespan(app):
    warmup()
    yield
    artifact.cache_clear()


app = FastAPI(title="API dedicada de modelo aprovado", lifespan=lifespan)
app.add_middleware(BodyLimitMiddleware)


@app.get("/health")
def health():
    return {"status":"ok", "service":"model-api"}


@app.get("/ready")
def ready():
    try:
        warmup()
        key, version, deployment = identity()
        return {"status":"ready", "model_key":key, "version":version, "deployment_id":str(deployment)}
    except Exception:
        raise HTTPException(503, "Model unavailable, revoked or requires republication")


@app.post("/internal/predict", response_model=InferenceResponse, dependencies=[Depends(auth)])
def predict(body: InferenceRequest):
    key, version, deployment = identity()
    if body.model_key != key or body.deployment_id != deployment:
        raise HTTPException(409, "Request does not match this published model")
    try:
        result = infer(body)
        if result.registered_version != version:
            raise HTTPException(409, "Version changed; republish service")
        return result
    except ValueError:
        raise HTTPException(422, "Model not approved or incompatible with request")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, "Model dependency unavailable")
