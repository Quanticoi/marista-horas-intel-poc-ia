"""Small real API gate before broader campaign and failure acceptance."""
from uuid import uuid4
from src.workbench.journey_config import Settings
from src.workbench.operations_sdk import campaign,generate,await_job,call,report
from src.workbench.contract_review import fetch_payload,reconcile,preflight
from src.data.journey import extract

def main():
    cfg=Settings.load()
    preflight(cfg)
    _,snapshot=extract(cfg)
    correlation=str(uuid4());key="hi.demo.probe."+correlation[:8]
    result=campaign(cfg,dict(snapshot_id=snapshot["id"],cycle_code=cfg.cycle,model_keys=[key],requested_by="v2-probe",confirm_training=True),correlation,correlation)
    cid=result["campaign_id"]
    completed=await_job(cfg,f"/v1/training/campaigns/{cid}")
    items=call(cfg,"GET",f"/v1/training/campaigns/{cid}/items")
    report("probe-training",dict(campaign=completed,items=items),"PASS" if completed["status"]=="COMPLETED" else "FAIL")
    assert completed["status"]=="COMPLETED",items
    item=items[0]
    body=dict(cycle_code=cfg.cycle,snapshot_id=snapshot["id"],model_selectors=[dict(model_name=key,model_version=item["model_version"])],requested_by="v2-probe",confirm_demo=True)
    submitted=generate(cfg,body,correlation,correlation)
    finished=await_job(cfg,submitted["status_url"])
    report("probe-generation",dict(request=body,submission=submitted,status=finished),"PASS" if finished["status"]=="COMPLETED" else "FAIL")
    assert finished["status"]=="COMPLETED",finished
    duplicate=generate(cfg,body,correlation,correlation)
    assert duplicate["generation_job_id"]==submitted["generation_job_id"]
    pages,offers=fetch_payload(cfg,finished["proposal_id"])
    evidence=reconcile(cfg,finished["proposal_id"],pages,offers)
    print(report("probe-complete",dict(campaign_id=cid,proposal_id=finished["proposal_id"],pages=pages,reconciliation=evidence,idempotency="PASS")))

if __name__=="__main__":
    main()
