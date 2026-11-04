"""Human review is separate from training and DEMO inference authorization."""
from uuid import uuid4
from sqlalchemy import text
import mlflow
from src.persistence.db import engine,rows,audit
from src.operations.jobs import Conflict
from src.workbench.verification import verify_model_storage
from src.operations.training import trace_for

def request_review(body,correlation):
    with engine().begin() as con:
        record=dict(con.execute(text("""INSERT INTO planning.model_approval_requests
          (model_name,model_version,action,reason,requested_by,correlation_id)
          VALUES (:model_name,:model_version,:action,:reason,:requested_by,:correlation) RETURNING *"""),
          dict(**body,correlation=correlation)).mappings().one())
        audit(con,body["requested_by"],"MODEL_REVIEW_REQUESTED","approval",record["approval_id"],correlation,body)
    return record

def review(approval_id,actor,approve):
    client=mlflow.MlflowClient()
    with engine().begin() as con:
        request=con.execute(text("SELECT * FROM planning.model_approval_requests WHERE approval_id=:id FOR UPDATE"),{"id":approval_id}).mappings().first()
        if not request:
            raise LookupError("Review request not found")
        if request["status"]!="REQUESTED":
            raise Conflict("Review already decided")
        name=request["model_name"];version=request["model_version"]
        con.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"),{"key":"approval:"+name})
        current=con.execute(text("SELECT * FROM planning.model_approval_requests WHERE model_name=:name AND status='APPROVED'"),{"name":name}).mappings().first()
        status="REJECTED"
        digest=None;run_id=None
        if approve:
            if request["action"]=="REVOKE":
                if not current or current["model_version"]!=version:
                    raise Conflict("Selected version is not currently approved")
                con.execute(text("UPDATE planning.model_approval_requests SET status='REVOKED' WHERE approval_id=:id"),{"id":current["approval_id"]})
                client.delete_registered_model_alias(name,"champion")
                status="REVOKED"
            else:
                if request["action"]=="ROLLBACK" and not con.execute(text("SELECT 1 FROM planning.model_approval_requests WHERE model_name=:name AND model_version=:version AND status='REVOKED' LIMIT 1"),dict(name=name,version=version)).first():
                    raise Conflict("Rollback requires a previously approved version")
                registered=client.get_model_version(name,version)
                run=client.get_run(registered.run_id)
                if run.info.status!="FINISHED" or run.data.tags.get("mode")!="DEMO":
                    raise ValueError("Only finished traceable DEMO versions are eligible")
                trace=trace_for(client,registered)
                evidence=verify_model_storage(trace)
                digest=next(e["sha256"] for e in evidence if e["key"].endswith("/model.pkl"))
                if digest!=registered.tags.get("artifact_sha256"):
                    raise ValueError("Candidate artifact hash mismatch")
                run_id=registered.run_id
                con.execute(text("UPDATE planning.model_approval_requests SET status='REVOKED' WHERE model_name=:name AND status='APPROVED'"),{"name":name})
                client.set_registered_model_alias(name,"champion",version)
                status="APPROVED"
        con.execute(text("""UPDATE planning.model_approval_requests SET status=:status,reviewed_by=:actor,reviewed_at_utc=now(),
            prior_version=:prior,artifact_sha256=:digest,run_id=:run WHERE approval_id=:id"""),
            dict(status=status,actor=actor,prior=current["model_version"] if current else None,digest=digest,run=run_id,id=approval_id))
        audit(con,actor,"MODEL_REVIEW_"+status,"approval",approval_id,request["correlation_id"],
              {"model_name":name,"model_version":version,"action":request["action"]},request["reason"])
    return rows("SELECT * FROM planning.model_approval_requests WHERE approval_id=:id",{"id":approval_id})[0]
