"""Controlled real negative cases; requires the disposable project marker."""
import json
import os
from uuid import uuid4
import httpx
import mlflow
from sqlalchemy import text
from src.workbench.journey_config import Settings
from src.workbench.operations_sdk import call,campaign,await_job,generate,report
from src.data.journey import extract,prepare,FEATURES
from src.persistence.db import engine,rows
from src.data.storage import s3,bucket
from src.common.settings import required

def main():
    if os.getenv("POC_PROJECT")!="marista-correcoes-isolated":
        raise RuntimeError("Negative mutations allowed only in disposable isolated project")
    cfg=Settings.load();frame,snapshot=extract(cfg);_,_,future=prepare(frame,snapshot)
    mlflow.set_tracking_uri(cfg.tracking);client=mlflow.MlflowClient()
    stamp=uuid4().hex;name="hi.demo.negative."+stamp[:8];proof={}
    def train():
        submitted=campaign(cfg,dict(snapshot_id=snapshot["id"],cycle_code=cfg.cycle,model_keys=[name],requested_by="isolated-negative",confirm_training=True),str(uuid4()))
        assert await_job(cfg,f"/v1/training/campaigns/{submitted['campaign_id']}")["status"]=="COMPLETED"
        return call(cfg,"GET",f"/v1/training/campaigns/{submitted['campaign_id']}/items")[0]["result"]
    first=train();version=client.get_model_version(name,first["model_version"])
    artifact=next(p for p in first["storage_evidence"] if p["key"].endswith("/model.pkl"))
    storage=s3();blob=storage.get_object(Bucket=bucket(),Key=artifact["key"])["Body"].read()
    request=dict(execution_id=version.tags["execution_id"],model_name=name,model_version=version.version,run_id=version.run_id,
                 snapshot_id=snapshot["id"],records=future[FEATURES].head(1).to_dict("records"))
    try:
        storage.put_object(Bucket=bucket(),Key=artifact["key"],Body=b"ISOLATED CHECKSUM NEGATIVE TEST")
        response=httpx.post(cfg.inference+"/internal/draft/predict",json=request,headers={"Authorization":"Bearer "+required("INFERENCE_TOKEN")},timeout=60)
        assert response.status_code==409
        proof["corrupted_artifact"]={"status":"PASS","http_status":response.status_code,"model":name,"version":version.version}
        storage.delete_object(Bucket=bucket(),Key=artifact["key"])
        response=httpx.post(cfg.inference+"/internal/draft/predict",json=request,headers={"Authorization":"Bearer "+required("INFERENCE_TOKEN")},timeout=60)
        assert response.status_code==503
        proof["missing_artifact"]={"status":"PASS","http_status":response.status_code}
    finally:
        storage.put_object(Bucket=bucket(),Key=artifact["key"],Body=blob)
    response=httpx.post(cfg.inference+"/internal/draft/predict",json=request,headers={"Authorization":"Bearer "+required("INFERENCE_TOKEN")},timeout=60)
    assert response.status_code==200
    # Verify a corrupted actual immutable mapping is detected; restore within an exclusive test model.
    entity=rows("SELECT * FROM planning.lineage_entities WHERE entity_type='model' AND external_id=:id",{"id":name+"/"+version.version})[0]
    def mapping(attributes):
        with engine("migration").begin() as con:
            con.execute(text("ALTER TABLE planning.lineage_entities DISABLE TRIGGER trg_lineage_entity_immutable"))
            con.execute(text("UPDATE planning.lineage_entities SET attributes=CAST(:attrs AS jsonb) WHERE entity_id=:id"),dict(id=entity["entity_id"],attrs=json.dumps(attributes)))
            con.execute(text("ALTER TABLE planning.lineage_entities ENABLE TRIGGER trg_lineage_entity_immutable"))
    try:
        mapping(dict(entity["attributes"],run_id="0"*32))
        found=rows("SELECT attributes FROM planning.lineage_entities WHERE entity_id=:id",{"id":entity["entity_id"]})[0]
        assert found["attributes"]["run_id"]!=client.get_model_version(name,version.version).run_id
        proof["corrupted_mapping"]={"status":"PASS","integrity":"MISMATCH","entity_id":str(entity["entity_id"])}
    finally:
        mapping(entity["attributes"])
    # Shared persistence adapter must rollback header and all rows together.
    from src.persistence.journey import compose,persist
    invalid=compose(future,[10.0]*len(future));invalid[0]["discipline_id"]=str(uuid4())
    failed_id=str(uuid4())
    try:
        persist(cfg,failed_id,snapshot,dict(first,inference_id=str(uuid4())),invalid)
    except Exception:
        pass
    else:
        raise AssertionError("Invalid foreign key did not fail")
    assert not rows("SELECT execution_id FROM planning.proposal_generations WHERE execution_id=:id",{"id":failed_id})
    proof["transaction_rollback"]={"status":"PASS","proposal_id":failed_id,"persisted_headers":0}
    # Approval/rollback/revocation are explicit operator HTTP decisions.
    def review(version,action):
        request=call(cfg,"POST","/v1/governance/requests",dict(model_name=name,model_version=version,action=action,requested_by="isolated-test",reason="Explicit isolated governance acceptance"))
        return call(cfg,"POST",f"/v1/governance/requests/{request['approval_id']}/review",dict(approve=True,confirm="REVIEW_EXPLICIT_VERSION"),operator=True)
    approved=review(first["model_version"],"APPROVE")
    second=train();review(second["model_version"],"APPROVE")
    rolled=review(first["model_version"],"ROLLBACK")
    assert client.get_model_version_by_alias(name,"champion").version==first["model_version"]
    payload=dict(cycle_code=cfg.cycle,snapshot_id=snapshot["id"],model_selectors=[dict(model_name=name,model_version=first["model_version"])],mode="APPROVED",requested_by="isolated-test",confirm_demo=True)
    submitted=generate(cfg,payload,str(uuid4()))
    generated=await_job(cfg,submitted["status_url"]);assert generated["status"]=="COMPLETED"
    revoked=review(first["model_version"],"REVOKE")
    denied=httpx.post(cfg.api+"/v1/proposals/generations",json=payload,headers={"Authorization":"Bearer "+required("API_TOKEN"),"Idempotency-Key":str(uuid4())},timeout=30)
    assert denied.status_code==403
    proof["governance"]={"status":"PASS","approved":approved,"rollback":rolled,"revoked":revoked,"post_revoke_http":403,"approved_generation":generated}
    # Simulate commit-before-manifest interruption: remove only this test manifest and replay the same persisted job.
    job_id=generated["generation_job_id"];manifest_key=f"lineage/poc/planilha-turmas/proposals/{job_id}/revisions/1/manifest.json"
    storage.delete_object(Bucket=bucket(),Key=manifest_key)
    with engine().begin() as con:
        con.execute(text("UPDATE planning.operation_jobs SET status='PENDING',enqueued_at_utc=NULL,available_at_utc=now() WHERE job_id=:id"),{"id":job_id})
    repaired=await_job(cfg,submitted["status_url"])
    assert repaired["proposal_id"]==job_id
    storage.head_object(Bucket=bucket(),Key=manifest_key)
    assert rows("SELECT count(*) n FROM planning.proposal_generations WHERE execution_id=:id",{"id":job_id})[0]["n"]==1
    proof["manifest_repair"]={"status":"PASS","proposal_id":job_id,"headers":1,"artifact_key":manifest_key}
    print(report("lineage-negative-tests",proof))

if __name__=="__main__":
    main()
