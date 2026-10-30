"""Dedicated data intake and training metadata service; PostgreSQL is the only DB."""
import hmac
import uuid
import httpx
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.responses import JSONResponse
from mlflow import MlflowClient
from sqlalchemy import text
from src.common.settings import required
from src.common.http_limits import BodyLimitMiddleware
from src.data.pipeline import ingest, load
from src.data.storage import s3, bucket
from src.persistence.db import rows, engine
from src.ingestion.contracts import Dataset, TrainingStart

app = FastAPI(title="Entrada de dados e metadados de treinamento", version="2.0")
app.add_middleware(BodyLimitMiddleware, max_bytes=4 * 1024 * 1024)


def auth(authorization: str = Header(default="")):
    if not hmac.compare_digest(authorization, "Bearer " + required("INGESTION_TOKEN")):
        raise HTTPException(401, "Invalid ingestion token")


@app.exception_handler(ValueError)
async def invalid(request, error):
    return JSONResponse(status_code=422, content={"detail": str(error)})


@app.exception_handler(Exception)
async def unavailable(request, error):
    return JSONResponse(status_code=503, content={"detail": "Data dependency unavailable"})


@app.get("/health")
def health():
    return {"status": "ok", "service": "ingestion"}


@app.get("/ready")
def ready():
    rows("SELECT 1")
    s3().head_bucket(Bucket=bucket())
    httpx.get(required("MLFLOW_TRACKING_URI") + "/health", timeout=5).raise_for_status()
    return {"status": "ready"}


@app.post("/v1/datasets", dependencies=[Depends(auth)])
def receive(body: Dataset):
    cfg = dict(as_of_date=body.as_of_date.isoformat(), target_year=body.target_year, target_semester=body.target_semester)
    snapshot = ingest([r.model_dump() for r in body.records], cfg, body.source)
    return metadata(uuid.UUID(snapshot))


@app.get("/v1/datasets/{snapshot_id}", dependencies=[Depends(auth)])
def metadata(snapshot_id: uuid.UUID):
    found = rows("SELECT * FROM planning.dataset_snapshots WHERE id=:id AND sealed_at IS NOT NULL", {"id":snapshot_id})
    if not found:
        raise HTTPException(404, "Sealed snapshot not found")
    result = found[0]
    result["records"] = load(snapshot_id).to_dict("records")
    return result


@app.get("/v1/datasets", dependencies=[Depends(auth)])
def datasets():
    return rows("SELECT id,cycle_id,row_count,source_reference,sha256,as_of_date FROM planning.dataset_snapshots WHERE sealed_at IS NOT NULL ORDER BY created_at DESC LIMIT 100")


@app.post("/v1/training", dependencies=[Depends(auth)])
def start(body: TrainingStart):
    run = MlflowClient().get_run(body.run_id)
    expected = {"snapshot_id":str(body.snapshot_id), "model_key":body.model_key,
                "code_version":body.code_version, "config_hash":body.config_hash}
    if run.info.status != "RUNNING" or any(run.data.tags.get(k) != v for k, v in expected.items()):
        raise ValueError("Training/run provenance mismatch")
    with engine().begin() as con:
        con.execute(text("SELECT pg_advisory_xact_lock(76432)"))
        existing = con.execute(text("SELECT id FROM planning.training_executions WHERE mlflow_run_id=:run"), {"run":body.run_id}).scalar_one_or_none()
        if existing:
            return {"execution_id":str(existing)}
        active = con.execute(text("SELECT count(*) FROM planning.training_executions WHERE status='RUNNING'")).scalar_one()
        if active >= 2:
            raise HTTPException(409, "Two training runs active; finalize abandoned runs before retrying")
        model = con.execute(text("""SELECT m.id FROM planning.model_catalog m WHERE m.model_key=:key AND m.active
            AND EXISTS (SELECT 1 FROM planning.historical_enrollments h WHERE h.snapshot_id=:snapshot AND h.period_id=m.period_id)"""),
            {"key":body.model_key, "snapshot":body.snapshot_id}).scalar_one_or_none()
        if model is None:
            raise ValueError("Model is not in this dataset")
        execution = uuid.uuid4()
        con.execute(text("""INSERT INTO planning.training_executions
            (id,model_id,snapshot_id,mlflow_run_id,algorithm,code_version,config_hash,status,started_at)
            VALUES (:id,:model,:snapshot,:run,:algorithm,:code,:cfg,'RUNNING',now())"""),
            dict(id=execution,model=model,snapshot=body.snapshot_id,run=body.run_id,algorithm=body.algorithm,code=body.code_version,cfg=body.config_hash))
    return {"execution_id":str(execution)}


@app.post("/v1/training/{run_id}/sync", dependencies=[Depends(auth)])
def finish(run_id: str):
    if len(run_id) != 32 or any(c not in "0123456789abcdef" for c in run_id):
        raise ValueError("Invalid run ID")
    run = MlflowClient().get_run(run_id)
    if run.info.status not in ("FINISHED", "FAILED", "KILLED"):
        raise HTTPException(409, "Run has not finished")
    values = run.data.metrics
    with engine().begin() as con:
        result = con.execute(text("""UPDATE planning.training_executions SET status=:status,
            mae=:mae,rmse=:rmse,smape=:smape,duration_ms=:duration,finished_at=now()
            WHERE mlflow_run_id=:run AND status='RUNNING' RETURNING id"""),
            dict(status="COMPLETED" if run.info.status == "FINISHED" else "FAILED",run=run_id,
                 mae=values.get("mae"),rmse=values.get("rmse"),smape=values.get("smape"),
                 duration=(run.info.end_time or run.info.start_time)-run.info.start_time)).scalar_one_or_none()
        if result is None and not con.execute(text("SELECT id FROM planning.training_executions WHERE mlflow_run_id=:run"), {"run":run_id}).first():
            raise HTTPException(404, "Training record not found")
    return {"run_id":run_id, "status":run.info.status}
