"""Recoverable, fail-closed technical model review across SQL and MLflow.

SQL and the MLflow Registry are not in a distributed transaction. Preparation
commits a RECONCILING request and removes SQL approval before any alias change.
A retry of the same approval ID resumes synchronization; it never silently
re-approves the prior version.
"""
from sqlalchemy import text
import mlflow
from mlflow.exceptions import MlflowException
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


def alias_version(client,name):
    """None means no champion; other Registry errors must propagate."""
    try:
        return str(client.get_model_version_by_alias(name,"champion").version)
    except MlflowException as error:
        if error.error_code=="RESOURCE_DOES_NOT_EXIST":
            return None
        raise


def synchronize_alias(client,name,action,version,prior):
    """Idempotent external step. Never overwrite an unexpected concurrent alias."""
    observed=alias_version(client,name)
    target=None if action=="REVOKE" else str(version)
    if observed==target:
        return
    if observed!=(str(prior) if prior is not None else None):
        raise Conflict("Registry champion differs from the SQL review checkpoint")
    if action=="REVOKE":
        client.delete_registered_model_alias(name,"champion")
    else:
        client.set_registered_model_alias(name,"champion",version)
    if alias_version(client,name)!=target:
        raise Conflict("Registry champion synchronization not confirmed")


def review(approval_id,actor,approve):
    client=mlflow.MlflowClient()
    with engine().begin() as con:
        request=con.execute(text("SELECT * FROM planning.model_approval_requests WHERE approval_id=:id FOR UPDATE"),{"id":approval_id}).mappings().first()
        if not request:
            raise LookupError("Review request not found")
        status=request["status"]
        if status not in ("REQUESTED","RECONCILING"):
            raise Conflict("Review already decided")
        if status=="RECONCILING" and not approve:
            raise Conflict("Review synchronization already started; retry with approval")
        name=request["model_name"];version=request["model_version"]
        con.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"),{"key":"approval:"+name})
        if status=="REQUESTED":
            if not approve:
                con.execute(text("""UPDATE planning.model_approval_requests
                    SET status='REJECTED',reviewed_by=:actor,reviewed_at_utc=now()
                    WHERE approval_id=:id"""),{"id":approval_id,"actor":actor})
                audit(con,actor,"MODEL_REVIEW_REJECTED","approval",approval_id,request["correlation_id"])
                return rows("SELECT * FROM planning.model_approval_requests WHERE approval_id=:id",{"id":approval_id})[0]
            competing=con.execute(text("""SELECT approval_id FROM planning.model_approval_requests
                WHERE model_name=:name AND status='RECONCILING' FOR UPDATE"""),{"name":name}).first()
            if competing:
                raise Conflict("Another review for this model is awaiting Registry reconciliation")
            current=con.execute(text("""SELECT * FROM planning.model_approval_requests
                WHERE model_name=:name AND status='APPROVED' FOR UPDATE"""),{"name":name}).mappings().first()
            prior=current["model_version"] if current else None
            if request["action"]=="REVOKE":
                if prior is None or str(prior)!=str(version):
                    raise Conflict("Selected version is not currently approved")
                digest=None;run_id=None
            else:
                if request["action"]=="ROLLBACK" and not con.execute(text("""SELECT 1 FROM planning.model_approval_requests
                    WHERE model_name=:name AND model_version=:version AND status='REVOKED'
                    LIMIT 1"""),{"name":name,"version":version}).first():
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
            # Before the external mutation, make SQL reject *all* approved access
            # to this model. Only the final step establishes an APPROVED record.
            con.execute(text("""UPDATE planning.model_approval_requests SET status='REVOKED'
                WHERE model_name=:name AND status='APPROVED'"""),{"name":name})
            con.execute(text("""UPDATE planning.model_approval_requests
                SET status='RECONCILING',prior_version=:prior,artifact_sha256=:digest,
                    run_id=:run,reviewed_by=:actor
                WHERE approval_id=:id"""),dict(prior=prior,digest=digest,run=run_id,actor=actor,id=approval_id))
            audit(con,actor,"MODEL_REVIEW_RECONCILING","approval",approval_id,request["correlation_id"],
                  {"model_name":name,"model_version":version,"action":request["action"]})
    # The SQL preparation transaction is committed here. Registry calls are
    # outside DB transactions. A failure leaves RECONCILING, not APPROVED.
    synchronize_alias(client,name,request["action"],version,request["prior_version"] if status=="RECONCILING" else prior)
    with engine().begin() as con:
        pending=con.execute(text("""SELECT * FROM planning.model_approval_requests
            WHERE approval_id=:id FOR UPDATE"""),{"id":approval_id}).mappings().one()
        con.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"),{"key":"approval:"+name})
        if pending["status"]!="RECONCILING":
            raise Conflict("Review state changed before finalization")
        target=None if request["action"]=="REVOKE" else str(version)
        if alias_version(client,name)!=target:
            raise Conflict("Registry champion changed during finalization")
        final="REVOKED" if request["action"]=="REVOKE" else "APPROVED"
        con.execute(text("""UPDATE planning.model_approval_requests
            SET status=:status,reviewed_by=:actor,reviewed_at_utc=now()
            WHERE approval_id=:id AND status='RECONCILING'"""),
            dict(status=final,actor=actor,id=approval_id))
        audit(con,actor,"MODEL_REVIEW_"+final,"approval",approval_id,request["correlation_id"],
              {"model_name":name,"model_version":version,"action":request["action"]},request["reason"])
    return rows("SELECT * FROM planning.model_approval_requests WHERE approval_id=:id",{"id":approval_id})[0]
