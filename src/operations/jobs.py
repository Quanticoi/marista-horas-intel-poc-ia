"""Postgres owns state; durable Celery delivery is recoverable and deduplicated."""
import json
import threading
import time
from sqlalchemy import text
from src.persistence.db import engine,rows,audit
from src.common.lineage import sha256
from src.common.logging import event

class Conflict(ValueError):
    pass

def emit(con,kind,job=None,campaign=None,details=None):
    con.execute(text("INSERT INTO planning.operation_events(job_id,campaign_id,event_type,details) VALUES (:job,:campaign,:kind,CAST(:details AS jsonb))"),
        dict(job=job,campaign=campaign,kind=kind,details=json.dumps(details or {},default=str)))
    correlation=None
    if job:
        correlation=con.execute(text("SELECT correlation_id FROM planning.operation_jobs WHERE job_id=:id"),{"id":job}).scalar_one()
    elif campaign:
        correlation=con.execute(text("SELECT correlation_id FROM planning.training_campaigns WHERE campaign_id=:id"),{"id":campaign}).scalar_one()
    event("worker",kind,job_id=str(job) if job else None,campaign_id=str(campaign) if campaign else None,
          correlation_id=correlation,details=details or {})

def create(kind,payload,key,actor,correlation,con=None,campaign=None,model_key=None):
    if con is None:
        with engine().begin() as transaction:
            return create(kind,payload,key,actor,correlation,transaction,campaign,model_key)
    digest=sha256(payload)
    con.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"),{"key":kind+key})
    old=con.execute(text("SELECT * FROM planning.operation_jobs WHERE kind=:kind AND idempotency_key=:key"),dict(kind=kind,key=key)).mappings().first()
    if old:
        if old["request_hash"]!=digest:
            raise Conflict("Idempotency key reused with different payload")
        return dict(old)
    result=dict(con.execute(text("""INSERT INTO planning.operation_jobs
        (kind,request,request_hash,idempotency_key,requested_by,correlation_id,campaign_id,model_key,max_attempts)
        VALUES (:kind,CAST(:payload AS jsonb),:digest,:key,:actor,:correlation,:campaign,:model,:attempts) RETURNING *"""),
        dict(kind=kind,payload=json.dumps(payload),digest=digest,key=key,actor=actor,correlation=correlation,
             campaign=campaign,model=model_key,attempts=payload.get("max_attempts",3))).mappings().one())
    emit(con,"CREATED",result["job_id"],campaign)
    return result

def get(job_id):
    found=rows("SELECT * FROM planning.operation_jobs WHERE job_id=:id",{"id":job_id})
    if not found:
        raise LookupError("Job not found")
    return found[0]

def checkpoint(job_id,update):
    with engine().begin() as con:
        con.execute(text("UPDATE planning.operation_jobs SET result=result||CAST(:update AS jsonb),heartbeat_at_utc=now() WHERE job_id=:id"),
            dict(id=job_id,update=json.dumps(update,default=str)))
        emit(con,"CHECKPOINT",job_id,details={"fields":sorted(update)})

def submit(job_id):
    with engine().begin() as con:
        claimed=con.execute(text("""UPDATE planning.operation_jobs SET enqueued_at_utc=now() WHERE job_id=:id
          AND status IN ('PENDING','RUNNING') AND available_at_utc<=now()
          AND (enqueued_at_utc IS NULL OR enqueued_at_utc<now()-interval '60 seconds')
          AND (status='PENDING' OR heartbeat_at_utc<now()-interval '60 seconds') RETURNING job_id"""),{"id":job_id}).scalar_one_or_none()
        if claimed is None:
            return
    try:
        from src.workers.tasks import operation
        operation.delay(str(job_id))
    except Exception:
        with engine().begin() as con:
            con.execute(text("UPDATE planning.operation_jobs SET enqueued_at_utc=NULL WHERE job_id=:id"),{"id":job_id})
        event("worker","durable job awaits dispatcher",job_id=str(job_id),level="WARNING")

def create_campaign(body,key,correlation):
    payload=body.model_dump(mode="json")
    with engine().begin() as con:
        con.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"),{"key":"campaign:"+key})
        prior=con.execute(text("SELECT * FROM planning.training_campaigns WHERE idempotency_key=:key"),{"key":key}).mappings().first()
        if prior:
            if prior["request_hash"]!=sha256(payload):
                raise Conflict("Idempotency key reused with different payload")
            return dict(prior)
        campaign=dict(con.execute(text("""INSERT INTO planning.training_campaigns
            (idempotency_key,request_hash,request,correlation_id,requested_by,max_parallel_jobs,requested_count,status)
            VALUES (:key,:hash,CAST(:request AS jsonb),:correlation,:actor,:parallel,:count,'RUNNING') RETURNING *"""),
            dict(key=key,hash=sha256(payload),request=json.dumps(payload),correlation=correlation,actor=body.requested_by,
                 parallel=body.max_parallel_jobs,count=len(body.model_keys))).mappings().one())
        for model in body.model_keys:
            item={k:v for k,v in payload.items() if k!="model_keys"}
            item["model_key"]=model
            create("training",item,str(campaign["campaign_id"])+":"+model,body.requested_by,correlation,con,campaign["campaign_id"],model)
        emit(con,"CAMPAIGN_CREATED",campaign=campaign["campaign_id"])
    dispatch()
    return campaign

def campaign_state(campaign_id):
    found=rows("SELECT * FROM planning.training_campaigns WHERE campaign_id=:id",{"id":campaign_id})
    if not found:
        raise LookupError("Campaign not found")
    counts={r["status"]:r["n"] for r in rows("SELECT status,count(*) n FROM planning.operation_jobs WHERE campaign_id=:id GROUP BY status",{"id":campaign_id})}
    return dict(found[0],counts=counts)

def refresh_campaign(campaign_id):
    with engine().begin() as con:
        row=con.execute(text("SELECT * FROM planning.training_campaigns WHERE campaign_id=:id FOR UPDATE"),{"id":campaign_id}).mappings().one()
        counts={r.status:r.n for r in con.execute(text("SELECT status,count(*) n FROM planning.operation_jobs WHERE campaign_id=:id GROUP BY status"),{"id":campaign_id})}
        status=row["status"]
        running=counts.get("RUNNING",0); pending=counts.get("PENDING",0)
        if status=="PAUSING" and not running:
            status="PAUSED"
        elif status=="CANCELLING" and not running:
            status="CANCELLED"
        elif not running and not pending and status not in ("CANCELLED","PAUSED"):
            status="COMPLETED" if counts.get("COMPLETED",0)==row["requested_count"] else "PARTIAL" if counts.get("COMPLETED",0) else "FAILED"
        if status!=row["status"]:
            con.execute(text("UPDATE planning.training_campaigns SET status=:status,ended_at_utc=CASE WHEN :status IN ('COMPLETED','PARTIAL','FAILED','CANCELLED') THEN now() ELSE ended_at_utc END WHERE campaign_id=:id"),dict(id=campaign_id,status=status))
            emit(con,status,campaign=campaign_id,details=counts)

def control(campaign_id,action,actor):
    with engine().begin() as con:
        row=con.execute(text("SELECT * FROM planning.training_campaigns WHERE campaign_id=:id FOR UPDATE"),{"id":campaign_id}).mappings().first()
        if not row:
            raise LookupError("Campaign not found")
        allowed={"pause":("RUNNING",),"resume":("PAUSED","PAUSING"),"cancel":("RUNNING","PAUSING","PAUSED","CREATED"),"retry-failed":("FAILED","PARTIAL")}
        if row["status"] not in allowed[action]:
            raise Conflict("Campaign transition not allowed")
        status={"pause":"PAUSING","resume":"RUNNING","cancel":"CANCELLING","retry-failed":"RUNNING"}[action]
        if action=="cancel":
            con.execute(text("UPDATE planning.operation_jobs SET status='CANCELLED',ended_at_utc=now() WHERE campaign_id=:id AND status='PENDING'"),{"id":campaign_id})
        if action=="retry-failed":
            con.execute(text("UPDATE planning.operation_jobs SET status='PENDING',attempt=0,available_at_utc=now(),ended_at_utc=NULL WHERE campaign_id=:id AND status='FAILED'"),{"id":campaign_id})
        con.execute(text("UPDATE planning.training_campaigns SET status=:status,ended_at_utc=NULL WHERE campaign_id=:id"),dict(id=campaign_id,status=status))
        emit(con,action,campaign=campaign_id,details={"actor":actor})
        audit(con,actor,"CAMPAIGN_"+action.upper(),"campaign",campaign_id,str(campaign_id))
    refresh_campaign(campaign_id)
    dispatch()
    return campaign_state(campaign_id)

def dispatch():
    # Queue is transport only. Repeated delivery is safe under session advisory locks.
    for job in rows("""WITH ready AS (
        SELECT j.job_id,j.kind,COALESCE(c.max_parallel_jobs,2) AS slots,
          row_number() OVER (PARTITION BY j.campaign_id,j.kind ORDER BY j.status DESC,j.created_at_utc,j.job_id) AS position
        FROM planning.operation_jobs j LEFT JOIN planning.training_campaigns c USING(campaign_id)
        WHERE j.status='RUNNING' OR (j.status='PENDING' AND available_at_utc<=now()
          AND (j.campaign_id IS NULL OR c.status='RUNNING')))
        SELECT job_id FROM ready WHERE position<=slots LIMIT 60"""):
        submit(job["job_id"])

def process(job_id):
    with engine().connect() as lock:
        if not lock.execute(text("SELECT pg_try_advisory_lock(hashtext(:id))"),{"id":"operation:"+str(job_id)}).scalar_one():
            lock.commit();return
        lock.commit()
        stop=threading.Event()
        campaign=None
        try:
            with engine().begin() as con:
                campaign=con.execute(text("SELECT campaign_id FROM planning.operation_jobs WHERE job_id=:id"),{"id":job_id}).scalar_one()
                if campaign:
                    # Same lock order as pause/cancel: campaign before item.
                    state=con.execute(text("SELECT * FROM planning.training_campaigns WHERE campaign_id=:id FOR UPDATE"),{"id":campaign}).mappings().one()
                job=dict(con.execute(text("SELECT * FROM planning.operation_jobs WHERE job_id=:id FOR UPDATE"),{"id":job_id}).mappings().one())
                campaign=job["campaign_id"]
                if job["status"] in ("COMPLETED","CANCELLED","FAILED"):
                    return
                if not con.execute(text("SELECT available_at_utc<=now() FROM planning.operation_jobs WHERE job_id=:id"),{"id":job_id}).scalar_one():
                    return
                if campaign:
                    if job["status"]=="PENDING":
                        count=con.execute(text("SELECT count(*) FROM planning.operation_jobs WHERE campaign_id=:id AND status='RUNNING'"),{"id":campaign}).scalar_one()
                        if state["status"]!="RUNNING" or count>=state["max_parallel_jobs"]:
                            return
                    con.execute(text("UPDATE planning.training_campaigns SET started_at_utc=coalesce(started_at_utc,now()) WHERE campaign_id=:id"),{"id":campaign})
                if job["attempt"]>=job["max_attempts"]:
                    con.execute(text("UPDATE planning.operation_jobs SET status='FAILED',error_code='RETRY_EXHAUSTED',ended_at_utc=now() WHERE job_id=:id"),{"id":job_id})
                    return
                con.execute(text("UPDATE planning.operation_jobs SET status='RUNNING',attempt=attempt+1,started_at_utc=coalesce(started_at_utc,now()),heartbeat_at_utc=now() WHERE job_id=:id"),{"id":job_id})
                emit(con,"RUNNING",job_id,campaign,{"attempt":job["attempt"]+1})
            def heartbeat():
                while not stop.wait(10):
                    try:
                        with engine().begin() as con:
                            con.execute(text("UPDATE planning.operation_jobs SET heartbeat_at_utc=now() WHERE job_id=:id"),{"id":job_id})
                    except Exception:
                        pass  # The main transaction path decides failure; no secret-bearing exception logged.
            thread=threading.Thread(target=heartbeat,daemon=True);thread.start()
            started=time.monotonic()
            try:
                if job["kind"]=="generation":
                    from src.operations.generation import execute
                else:
                    from src.operations.training import execute
                import mlflow
                from src.common.settings import required
                from src.common.tracing import safe_span
                client=mlflow.MlflowClient()
                experiment=client.get_experiment_by_name(required("MLFLOW_EXPERIMENT_NAME"))
                if experiment is None:
                    mlflow.set_experiment(required("MLFLOW_EXPERIMENT_NAME"))
                    experiment=client.get_experiment_by_name(required("MLFLOW_EXPERIMENT_NAME"))
                with safe_span("worker."+job["kind"],{"job_id":str(job_id),"correlation_id":job["correlation_id"]},experiment.experiment_id) as span:
                    mlflow.update_current_trace(tags={"job_id":str(job_id),"correlation_id":job["correlation_id"],
                        "training_campaign_id":str(campaign) if campaign else "none"})
                    checkpoint(job_id,{"trace_id":span.trace_id})
                    result=execute(job)
                    if result.get("proposal_id"):
                        mlflow.update_current_trace(tags={"proposal_id":result["proposal_id"]})
                    if result.get("run_id"):
                        mlflow.update_current_trace(tags={"run_id":result["run_id"],"model_key":result["model_name"],"model_version":result["model_version"]})
                with engine().begin() as con:
                    con.execute(text("UPDATE planning.operation_jobs SET status='COMPLETED',result=result||CAST(:result AS jsonb),ended_at_utc=now(),error_code=NULL WHERE job_id=:id"),dict(id=job_id,result=json.dumps(result,default=str)))
                    emit(con,"COMPLETED",job_id,campaign,{"seconds":time.monotonic()-started})
            except Exception as error:
                with engine().begin() as con:
                    con.execute(text("""UPDATE planning.operation_jobs SET status=CASE WHEN attempt>=max_attempts THEN 'FAILED' ELSE 'PENDING' END,
                        error_code=:error,available_at_utc=now()+make_interval(secs=>LEAST(60,attempt*10)),
                        ended_at_utc=CASE WHEN attempt>=max_attempts THEN now() ELSE NULL END WHERE job_id=:id"""),dict(id=job_id,error=type(error).__name__))
                    emit(con,"ATTEMPT_FAILED",job_id,campaign,{"error":type(error).__name__})
                event("worker","operation attempt failed",job_id=str(job_id),error=type(error).__name__,level="ERROR")
            finally:
                stop.set();thread.join(timeout=2)
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(hashtext(:id))"),{"id":"operation:"+str(job_id)})
            lock.commit()
            if campaign:
                refresh_campaign(campaign)
    return True
