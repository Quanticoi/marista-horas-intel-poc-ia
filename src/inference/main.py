import hmac
import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, HTTPException
from src.common.settings import required
from src.common.http_limits import BodyLimitMiddleware
from src.common.logging import event
from src.data.storage import s3, bucket
from src.persistence.db import rows
from src.inference.contracts import InferenceRequest, InferenceResponse
from src.inference.routing import route as infer

@asynccontextmanager
async def lifespan(app):
    from src.inference.academic import preload
    preload()
    yield


app = FastAPI(title="Modelos de Inferência — serviço interno", docs_url=None, redoc_url=None,lifespan=lifespan)
app.add_middleware(BodyLimitMiddleware)
from src.common.tracing import install_http_tracing
install_http_tracing(app, "inference", "/internal/")


def auth(authorization: str = Header(default="")):
    if not hmac.compare_digest(authorization, "Bearer " + required("INFERENCE_TOKEN")):
        raise HTTPException(401, "Invalid service token")


from src.inference.journey import router as draft_router
app.include_router(draft_router(auth))
from src.inference.academic import router as academic_router
app.include_router(academic_router(auth))


@app.get("/health")
def health():
    return {"status": "ok", "service": "inference"}


@app.get("/ready")
def ready():
    try:
        rows("SELECT 1", role="readonly")
        s3().head_bucket(Bucket=bucket())
        httpx.get(required("MLFLOW_TRACKING_URI") + "/health", timeout=5).raise_for_status()
    except Exception:
        raise HTTPException(503, "Model dependencies unavailable")
    return {"status": "ready"}


@app.post("/internal/predict", response_model=InferenceResponse, dependencies=[Depends(auth)])
def predict(body: InferenceRequest):
    try:
        result = infer(body)
        event("inference", "model executed", model_key=body.model_key,
              deployment_id=str(body.deployment_id), snapshot_id=str(body.snapshot_id))
        return result
    except ValueError:
        raise HTTPException(422, "Model not approved or incompatible with request")
    except Exception as error:
        event("inference", "execution failed", level="ERROR", error=type(error).__name__)
        raise HTTPException(503, "Model dependency unavailable")
