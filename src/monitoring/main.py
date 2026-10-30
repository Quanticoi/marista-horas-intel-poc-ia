"""Always-on observation pod; no training, promotion or mutation endpoints."""
import asyncio
import hmac
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, Header, HTTPException
from src.common.settings import required
from src.common.logging import event
from src.monitoring.quality import monitor
from src.persistence.db import rows

state = {"status": "starting", "sampled_at": None, "quality": []}


def sample():
    return {"status": "ready", "sampled_at": datetime.now(timezone.utc).isoformat(),
            "quality": monitor(),
            "training": rows("SELECT status,count(*) AS count FROM planning.training_executions GROUP BY status", role="readonly"),
            "deployments": rows("SELECT status,count(*) AS count FROM planning.model_deployments GROUP BY status", role="readonly")}


async def poll():
    global state
    while True:
        try:
            state = await asyncio.to_thread(sample)
            event("monitoramento", "quality observation", evaluations=len(state["quality"]))
        except Exception as error:
            state = {**state, "status": "error"}
            event("monitoramento", "observation failed", level="ERROR", error=type(error).__name__)
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(poll())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="Monitoramento MLOps", lifespan=lifespan, docs_url=None, redoc_url=None)


def auth(authorization: str = Header(default="")):
    if not hmac.compare_digest(authorization, "Bearer " + required("MONITOR_TOKEN")):
        raise HTTPException(401, "Invalid service token")


@app.get("/health")
def health():
    return {"status": "ok", "service": "monitoramento"}


@app.get("/ready")
def ready():
    if state["status"] != "ready":
        raise HTTPException(503, "Waiting for successful observation")
    return {"status": "ready", "sampled_at": state["sampled_at"]}


@app.get("/v1/status", dependencies=[Depends(auth)])
def status():
    return state
