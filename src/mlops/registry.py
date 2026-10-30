import uuid
from mlflow import MlflowClient
from sqlalchemy import text
from src.persistence.db import engine, audit


def promote(key, version, actor, reason):
    if not actor.strip() or not reason.strip():
        raise ValueError("Operator and justification required")
    client = MlflowClient()
    candidate = client.get_model_version(key, str(version))
    from src.mlops.artifacts import load_bundle
    _, info = load_bundle(candidate.source, candidate.tags.get("bundle_sha256"), deserialize=False)
    if info["model_key"] != key or info["run_id"] != candidate.run_id:
        raise ValueError("Model artifact provenance mismatch")
    if client.get_run(candidate.run_id).info.status != "FINISHED":
        raise ValueError("Training run has not finished successfully")
    with engine().begin() as con:
        con.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": key})
        model = con.execute(text("SELECT * FROM planning.model_catalog WHERE model_key=:key"), {"key": key}).mappings().one()
        execution = con.execute(text("SELECT id,snapshot_id,code_version,config_hash FROM planning.training_executions WHERE model_id=:id AND mlflow_run_id=:run AND status='COMPLETED'"),
                                dict(id=model["id"], run=candidate.run_id)).first()
        if not execution:
            raise ValueError("Version has no completed traceable training")
        if str(execution.snapshot_id) != info["snapshot_id"] or execution.code_version != info["code_version"] or execution.config_hash != info["config_hash"]:
            raise ValueError("Training/binary provenance mismatch")
        snapshot_hash = con.execute(text("SELECT sha256 FROM planning.dataset_snapshots WHERE id=:id AND sealed_at IS NOT NULL"), {"id":execution.snapshot_id}).scalar_one()
        if snapshot_hash != info["dataset_sha256"]:
            raise ValueError("Dataset/binary checksum mismatch")
        # A failed commit leaves the alias inconsistent; inference fails closed and reconcile repairs it.
        con.execute(text("UPDATE planning.model_deployments SET status='REVOKED',revoked_at=now() WHERE model_id=:id AND alias='champion' AND status='APPROVED'"), {"id": model["id"]})
        deployment = uuid.uuid4()
        con.execute(text("""INSERT INTO planning.model_deployments
           (id,model_id,registered_version,artifact_uri,alias,status,approved_by,justification,
            mlflow_run_id,code_version,dataset_sha256,artifact_sha256)
           VALUES (:id,:model,:version,:uri,'champion','APPROVED',:actor,:reason,:run,:code,:dataset,:sha)"""),
           dict(id=deployment, model=model["id"], version=str(version), uri=candidate.source, actor=actor, reason=reason,
                run=candidate.run_id,code=info["code_version"],dataset=info["dataset_sha256"],sha=candidate.tags["bundle_sha256"]))
        audit(con, actor, "MODEL_PROMOTED", "deployment", deployment, str(deployment), {"version": version}, reason)
        client.set_registered_model_alias(key, "champion", str(version))
    return str(deployment)


def reconcile(key, actor, reason):
    if not actor.strip() or not reason.strip():
        raise ValueError("Operator and justification required")
    with engine().begin() as con:
        con.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": key})
        row = con.execute(text("""SELECT d.* FROM planning.model_deployments d JOIN planning.model_catalog m ON m.id=d.model_id
          WHERE m.model_key=:key AND d.status='APPROVED' AND d.alias='champion'"""), {"key": key}).mappings().one()
        MlflowClient().set_registered_model_alias(key, "champion", row["registered_version"])
        audit(con, actor, "ALIAS_RECONCILED", "deployment", row["id"], str(uuid.uuid4()), reason=reason)
