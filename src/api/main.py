import hmac
import re
import uuid
from typing import Annotated
from fastapi import FastAPI, Depends, Header, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ConfigDict
from src.common.http_limits import BodyLimitMiddleware
from src.common.settings import required
from src.common.logging import event
from src.persistence.db import rows
from src.inference.service import create_job, process

app = FastAPI(title="PUCPR Horários Inteligentes — dados sintéticos", version="1.0.0")
app.add_middleware(BodyLimitMiddleware)
from src.common.tracing import install_http_tracing
install_http_tracing(app, "api", "/v1/proposals")


def auth(authorization: str = Header(default="")):
    if not hmac.compare_digest(authorization, "Bearer "+required("API_TOKEN")):
        raise HTTPException(401, "Invalid token")


from src.api.proposals import router as proposal_router
app.include_router(proposal_router(auth))


@app.middleware("http")
async def correlation(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    if not re.fullmatch(r"[a-zA-Z0-9_.-]{1,120}", cid):
        return JSONResponse(status_code=422, content=dict(code="INVALID_CORRELATION",message="Invalid correlation ID",correlation_id=""))
    request.state.correlation_id = cid
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    event("api", "request", correlation_id=cid, method=request.method, path=request.url.path, status=response.status_code)
    return response


@app.exception_handler(HTTPException)
@app.exception_handler(RequestValidationError)
@app.exception_handler(ValueError)
async def invalid(request, error):
    return JSONResponse(status_code=getattr(error,"status_code",422), content=dict(
        code="REQUEST_ERROR",message=str(getattr(error,"detail","Invalid request")),correlation_id=getattr(request.state,"correlation_id","")))


@app.exception_handler(Exception)
async def unexpected(request, error):
    event("api", "request failed", level="ERROR", error=type(error).__name__,correlation_id=getattr(request.state,"correlation_id",""))
    return JSONResponse(status_code=503, content=dict(code="DEPENDENCY_ERROR",message="Service unavailable",correlation_id=getattr(request.state,"correlation_id","")))


@app.get("/health")
def health():
    return {"status":"ok", "synthetic":True}


@app.get("/ready")
def ready():
    try:
        rows("SELECT 1")
        import httpx
        import os
        httpx.get(os.environ["MLFLOW_TRACKING_URI"]+"/health", timeout=3).raise_for_status()
        httpx.get(required("INFERENCE_URI")+"/ready", timeout=15).raise_for_status()
        from src.workers.tasks import app as celery
        with celery.connection_for_write() as connection:
            connection.ensure_connection(max_retries=0)
        return {"status":"ready"}
    except Exception:
        raise HTTPException(503,"Dependencies unavailable")


@app.get("/v1/models", dependencies=[Depends(auth)])
def models():
    return rows("""SELECT m.*,d.registered_version,d.id AS deployment_id FROM planning.model_catalog m
      LEFT JOIN planning.model_deployments d ON d.model_id=m.id AND d.alias='champion' AND d.status='APPROVED' ORDER BY m.model_key""")


@app.get("/v1/models/{model_key}", dependencies=[Depends(auth)])
def model(model_key: str):
    found = [row for row in models() if row["model_key"] == model_key]
    if not found:
        raise HTTPException(404,"Model not found")
    found[0]["training"] = rows("SELECT * FROM planning.training_executions WHERE model_id=:id ORDER BY started_at DESC LIMIT 10", {"id":found[0]["id"]})
    return found[0]


class Batch(BaseModel):
    model_config = ConfigDict(extra='forbid')
    cycle_id: uuid.UUID
    snapshot_id: uuid.UUID
    requested_by: str = Field(min_length=1,max_length=120)


class Predict(Batch):
    model_key: str = Field(min_length=1,max_length=160)


@app.post("/v1/inference/batch", status_code=202, dependencies=[Depends(auth)])
def batch(body: Batch, request: Request, idempotency_key: str = Header(min_length=1,max_length=160)):
    job = create_job(body.cycle_id,body.snapshot_id,idempotency_key,body.requested_by,request.state.correlation_id)
    try:
        from src.workers.tasks import predict
        predict.delay(str(job["id"]))
    except Exception:
        event("api","publish pending; recover job required",level="WARNING",job_id=str(job["id"]))
    return {"job_id":job["id"],"status":job["status"]}


@app.post("/v1/inference/predict", dependencies=[Depends(auth)])
def predict_sync(body: Predict, request: Request):
    job = create_job(body.cycle_id,body.snapshot_id,str(uuid.uuid4()),body.requested_by,request.state.correlation_id,body.model_key)
    process(job["id"])
    output = results(job["id"],100,0)
    if not output:
        raise HTTPException(422,"No approved compatible model or inference failed")
    return output[0]


@app.get("/v1/jobs/{job_id}", dependencies=[Depends(auth)])
def job(job_id: uuid.UUID):
    found = rows("SELECT * FROM planning.prediction_jobs WHERE id=:id", {"id":job_id})
    if not found:
        raise HTTPException(404,"Job not found")
    return found[0]


@app.get("/v1/jobs/{job_id}/results", dependencies=[Depends(auth)])
def results(job_id: uuid.UUID, limit: int=Query(100,ge=1,le=100), offset: int=Query(0,ge=0,le=100000)):
    if job(job_id)["status"] in ("PENDING","RUNNING"):
        raise HTTPException(409,"Job not finished")
    return rows("""SELECT p.*,d.registered_version,d.mlflow_run_id,d.code_version,d.dataset_sha256,d.artifact_sha256 FROM planning.predictions p JOIN planning.model_deployments d
      ON d.id=p.deployment_id WHERE p.job_id=:id ORDER BY p.id LIMIT :limit OFFSET :offset""", dict(id=job_id,limit=limit,offset=offset))


@app.get("/v1/predictions", dependencies=[Depends(auth)])
def predictions(cycle_id: uuid.UUID|None=None, limit: int=Query(100,ge=1,le=100), offset: int=Query(0,ge=0,le=100000)):
    return rows("SELECT * FROM planning.predictions WHERE (CAST(:cycle AS uuid) IS NULL OR cycle_id=:cycle) ORDER BY predicted_at DESC,id LIMIT :limit OFFSET :offset",dict(cycle=cycle_id,limit=limit,offset=offset))


@app.get("/v1/monitoring/models", dependencies=[Depends(auth)])
def quality():
    return rows("SELECT * FROM planning.model_quality_evaluations ORDER BY evaluated_at DESC LIMIT 100")
