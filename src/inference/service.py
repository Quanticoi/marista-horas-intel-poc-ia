import json
import math
import uuid
from sqlalchemy import text
from src.persistence.db import engine, rows, audit
from src.inference.client import predict_remote
from src.inference.contracts import InferenceRequest


def create_job(cycle_id, snapshot_id, key, actor, correlation, model_key=None):
    # requested models stored in append-only audit so retries cannot change the request.
    with engine().begin() as con:
        con.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": "job-"+key})
        old = con.execute(text("SELECT * FROM planning.prediction_jobs WHERE idempotency_key=:key"), {"key": key}).mappings().first()
        if old:
            request = con.execute(text("SELECT new_value FROM planning.audit_events WHERE entity_id=:id AND event_type='JOB_CREATED' ORDER BY id LIMIT 1"),
                                  {"id": str(old["id"])}).scalar_one()
            if str(old["cycle_id"]) != str(cycle_id) or str(old["snapshot_id"]) != str(snapshot_id) or request["model_key"] != model_key:
                raise ValueError("Idempotency key reused with different payload")
            return dict(old)
        cycle = con.execute(text("SELECT * FROM planning.academic_cycles WHERE id=:id"), {"id": cycle_id}).mappings().one_or_none()
        snapshot = con.execute(text("SELECT * FROM planning.dataset_snapshots WHERE id=:id AND sealed_at IS NOT NULL"), {"id": snapshot_id}).mappings().one_or_none()
        if cycle is None or snapshot is None:
            raise ValueError("Cycle or sealed snapshot not found")
        target = cycle["target_year"]*2+cycle["target_semester"]-1
        if snapshot["as_of_date"].year*2+(snapshot["as_of_date"].month>6) >= target:
            raise ValueError("Snapshot must precede target cycle")
        count = con.execute(text("SELECT count(*) FROM planning.model_catalog WHERE active AND (CAST(:key AS text) IS NULL OR model_key=:key)"), {"key": model_key}).scalar_one()
        if not count or count > 30:
            raise ValueError("Model count outside 1..30")
        job_id = uuid.uuid4()
        job = con.execute(text("""INSERT INTO planning.prediction_jobs
          (id,cycle_id,snapshot_id,idempotency_key,correlation_id,status,requested_by,total_models)
          VALUES (:id,:cycle,:snapshot,:key,:correlation,'PENDING',:actor,:count) RETURNING *"""),
          dict(id=job_id,cycle=cycle_id,snapshot=snapshot_id,key=key,correlation=correlation,actor=actor,count=count)).mappings().one()
        audit(con, actor, "JOB_CREATED", "job", job_id, correlation, {"model_key": model_key})
        return dict(job)


def predict_one(con, job, model):
    con.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": model["model_key"]})
    deployment = con.execute(text("SELECT * FROM planning.model_deployments WHERE model_id=:id AND alias='champion' AND status='APPROVED'"), {"id":model["id"]}).mappings().one()
    cycle = con.execute(text("SELECT * FROM planning.academic_cycles WHERE id=:id"), {"id":job["cycle_id"]}).mappings().one()
    result = predict_remote(InferenceRequest(deployment_id=deployment["id"],
        snapshot_id=job["snapshot_id"], model_key=model["model_key"],
        target_year=cycle["target_year"], target_semester=cycle["target_semester"]))
    if result.registered_version != deployment["registered_version"]:
        raise ValueError("Inference version mismatch")
    raw = result.forecast_raw
    if not math.isfinite(raw):
        raise ValueError("Non-finite forecast")
    total = max(0, round(raw))
    prediction_id = uuid.uuid4()
    inserted = con.execute(text("""INSERT INTO planning.predictions
      (id,job_id,model_id,deployment_id,cycle_id,snapshot_id,campus_id,course_id,period_id,forecast_students,forecast_raw,is_fallback)
      VALUES (:id,:job,:model,:deployment,:cycle,:snapshot,:campus_id,:course_id,:period_id,:total,:raw,:fallback)
      ON CONFLICT (job_id,model_id) DO NOTHING RETURNING id"""),
      dict(id=prediction_id,job=job["id"],model=model["id"],deployment=deployment["id"],cycle=job["cycle_id"],
           snapshot=job["snapshot_id"],total=total,raw=raw,fallback=result.is_fallback,
           **{k:model[k] for k in ("campus_id","course_id","period_id")})).scalar_one_or_none()
    if inserted is None:
        return
    disciplines = con.execute(text("""SELECT d.* FROM planning.disciplines d JOIN planning.period_disciplines pd
      ON pd.discipline_id=d.id WHERE pd.period_id=:id"""), {"id":model["period_id"]}).mappings()
    # Synthetic rule: each discipline receives the full period cohort; 85/10/remainder percent.
    regular, dependency = int(total*.85), int(total*.10)
    for disc in disciplines:
        con.execute(text("""INSERT INTO planning.offer_suggestions
          (id,prediction_id,cycle_id,discipline_id,estimated_regular,estimated_dependency,estimated_elective,estimated_total,suggested_groups,status)
          VALUES (:id,:prediction,:cycle,:disc,:regular,:dependency,:elective,:total,:groups,'SUGGESTED')"""),
          dict(id=uuid.uuid4(),prediction=prediction_id,cycle=job["cycle_id"],disc=disc["id"],regular=regular,
               dependency=dependency,elective=total-regular-dependency,total=total,groups=max(1,math.ceil(total/disc["modulation_limit"]))))


def process(job_id):
    # Session advisory lock protects against duplicate Celery delivery across model transactions.
    with engine().connect() as lock:
        acquired = lock.execute(text("SELECT pg_try_advisory_lock(hashtext(:key))"), {"key":str(job_id)}).scalar_one()
        lock.commit()
        if not acquired:
            return
        try:
            job = rows("SELECT * FROM planning.prediction_jobs WHERE id=:id", {"id":job_id})[0]
            if job["status"] in ("COMPLETED", "PARTIAL_SUCCESS", "FAILED"):
                return
            request = rows("SELECT new_value FROM planning.audit_events WHERE entity_id=:id AND event_type='JOB_CREATED' ORDER BY id LIMIT 1", {"id":str(job_id)})[0]["new_value"]
            models = rows("SELECT * FROM planning.model_catalog WHERE active AND (CAST(:key AS text) IS NULL OR model_key=:key)", {"key":request["model_key"]})
            with engine().begin() as con:
                con.execute(text("UPDATE planning.prediction_jobs SET status='RUNNING',started_at=coalesce(started_at,now()) WHERE id=:id"), {"id":job_id})
            failed = []
            for model in models:
                if rows("SELECT id FROM planning.predictions WHERE job_id=:job AND model_id=:model", {"job":job_id,"model":model["id"]}):
                    continue
                try:
                    with engine().begin() as con:
                        predict_one(con, job, model)
                except Exception as error:
                    failed.append({"model_key":model["model_key"],"error":type(error).__name__})
            count = rows("SELECT count(*) AS n FROM planning.predictions WHERE job_id=:id", {"id":job_id})[0]["n"]
            status = "COMPLETED" if not failed else "PARTIAL_SUCCESS" if count else "FAILED"
            with engine().begin() as con:
                con.execute(text("""UPDATE planning.prediction_jobs SET status=:status,completed_models=:count,
                  failed_models=:failed,error_summary=:errors,finished_at=now() WHERE id=:id"""),
                  dict(id=job_id,status=status,count=count,failed=len(failed),errors=json.dumps(failed)))
                audit(con, "worker", "JOB_FINISHED", "job", job_id, job["correlation_id"], {"status":status,"failures":failed})
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(hashtext(:key))"), {"key":str(job_id)})
            lock.commit()
