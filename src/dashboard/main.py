import hmac
import json
import os
from collections import deque
from pathlib import Path
from fastapi import FastAPI, Depends, Header, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from src.common.settings import required
from src.persistence.db import rows

DIRECTORY = Path(os.getenv("LOG_DIRECTORY", "/logs"))

app = FastAPI(title="Operação POC")
STATIC = Path(__file__).parent/"static"
app.mount("/static",StaticFiles(directory=STATIC),name="static")


def auth(authorization: str=Header(default="")):
    if not hmac.compare_digest(authorization,"Bearer "+required("DASHBOARD_TOKEN")):
        raise HTTPException(401,"Token inválido")


@app.get("/")
def home():
    if os.getenv("RUNTIME") == "compose":
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        return HTMLResponse(html.replace('<body>', '<body><p role="status">Docker Compose: eventos atuais da jornada, API e inferência disponíveis por correlation_id. Logs completos: docker compose logs -f.</p>'))
    return FileResponse(STATIC/"index.html")


@app.get("/health")
def health():
    return {"status":"ok"}


@app.get("/ready")
def ready():
    if not DIRECTORY.is_dir() or not os.access(DIRECTORY,os.R_OK):
        raise HTTPException(503,"Log volume unavailable")
    return health()


@app.get("/api/logs",dependencies=[Depends(auth)])
def logs(namespace: str="", service: str="", pod: str="", level: str="", correlation_id: str="",
         q: str=Query("",max_length=200), since: str="", until: str="", limit: int=Query(100,ge=1,le=1000)):
    output = deque(maxlen=limit)
    filters = dict(namespace=namespace,service=service,pod=pod,level=level,correlation_id=correlation_id)
    # Bounded to 20 MiB per request; older data retained on PVC can be retrieved by backup.
    remaining = 20*1024*1024
    for path in sorted(DIRECTORY.glob("*.jsonl"),key=lambda p:p.stat().st_mtime,reverse=True):
        with path.open("rb") as stream:
            size=path.stat().st_size
            start=max(0,size-remaining)
            stream.seek(start)
            if start:
                stream.readline()
            data=stream.read(remaining)
            remaining-=len(data)
        for line in reversed(data.decode("utf-8",errors="replace").splitlines()):
            try:
                row=json.loads(line)
            except ValueError:
                continue
            if any(v and str(row.get(k,""))!=v for k,v in filters.items()):
                continue
            if q and q.lower() not in str(row.get("message","")).lower():
                continue
            if since and row.get("timestamp","") < since or until and row.get("timestamp","") > until:
                continue
            output.append(row)
            if len(output)==limit:
                return list(output)
        if remaining <= 0:
            break
    return list(output)


@app.get("/api/logs/stream",dependencies=[Depends(auth)])
def stream_logs():
    return StreamingResponse(iter(["data: "+json.dumps(logs(limit=100,q=""))+"\n\n"]),media_type="text/event-stream")


@app.get("/api/runtime/resources",dependencies=[Depends(auth)])
def resources():
    return [dict(kind="Compose", name="Local", status="Consulte docker compose ps; logs via compose logs")]


@app.get("/api/jobs",dependencies=[Depends(auth)])
def jobs():
    return rows("SELECT * FROM planning.prediction_jobs ORDER BY requested_at DESC LIMIT 100",role="readonly")


@app.get("/api/models",dependencies=[Depends(auth)])
def models():
    return rows("""SELECT m.model_key,d.registered_version,d.status FROM planning.model_catalog m LEFT JOIN planning.model_deployments d
       ON d.model_id=m.id AND d.alias='champion' AND d.status='APPROVED' ORDER BY m.model_key""",role="readonly")


@app.get("/api/campaigns",dependencies=[Depends(auth)])
def campaigns():
    return rows("""SELECT c.campaign_id,c.status,c.correlation_id,c.requested_count,
        count(j.job_id) FILTER(WHERE j.status='COMPLETED') AS completed,
        count(j.job_id) FILTER(WHERE j.status='FAILED') AS failed,
        count(j.job_id) FILTER(WHERE j.status='RUNNING') AS running
        FROM planning.training_campaigns c LEFT JOIN planning.operation_jobs j USING(campaign_id)
        GROUP BY c.campaign_id ORDER BY c.created_at_utc DESC LIMIT 100""",role="readonly")

@app.get("/api/operations",dependencies=[Depends(auth)])
def operations():
    return rows("""SELECT job_id,kind,status,correlation_id,campaign_id,attempt,
        result->>'proposal_id' AS proposal_id,result->>'trace_id' AS trace_id,error_code
        FROM planning.operation_jobs ORDER BY created_at_utc DESC LIMIT 100""",role="readonly")


@app.get("/api/health/services",dependencies=[Depends(auth)])
def services():
    import socket
    import httpx
    result={}
    from urllib.parse import urlparse
    storage=urlparse(required("MLFLOW_S3_ENDPOINT_URL"))
    for name,host,port in [("PostgreSQL",os.getenv("DB_HOST","postgres"),5432),
                           ("RabbitMQ",os.getenv("RABBITMQ_HOST","rabbitmq"),5672),
                           ("RustFS",storage.hostname,storage.port or (443 if storage.scheme == 'https' else 80))]:
        try:
            with socket.create_connection((host,port),timeout=3):
                result[name]="PASS TCP (não valida credenciais)"
        except OSError:
            result[name]="FAIL"
    for name,url in [("API",required("API_URI")+"/ready"),
                     ("MLflow",required("MLFLOW_TRACKING_URI")+"/health"),
                     ("Inferência",required("INFERENCE_URI")+"/ready"),
                     ("Monitoramento",os.getenv("MONITOR_URI","http://monitoramento:8010")+"/ready")]:
        try:
            httpx.get(url,timeout=5).raise_for_status()
            result[name]="PASS"
        except Exception:
            result[name]="FAIL"
    return result
