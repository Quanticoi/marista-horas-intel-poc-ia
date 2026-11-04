"""Real application HTTP, queue, database, Registry and artifact contract."""
from uuid import uuid4
import httpx
import pytest
from src.common.settings import required
from src.workbench.journey_config import Settings
from src.data.journey import extract
from src.workbench.operations_sdk import campaign,await_job,call,generate

@pytest.fixture(scope="module")
def scenario():
    cfg=Settings.load();_,snapshot=extract(cfg)
    key=uuid4().hex;name="hi.demo.integration."+key[:8]
    submitted=campaign(cfg,dict(snapshot_id=snapshot["id"],cycle_code=cfg.cycle,model_keys=[name],requested_by="pytest",confirm_training=True),"train-"+key)
    cid=submitted["campaign_id"]
    assert await_job(cfg,f"/v1/training/campaigns/{cid}")["status"]=="COMPLETED"
    item=call(cfg,"GET",f"/v1/training/campaigns/{cid}/items")[0]
    payload=dict(cycle_code=cfg.cycle,snapshot_id=snapshot["id"],model_selectors=[dict(model_name=name,model_version=item["model_version"])],requested_by="pytest",confirm_demo=True)
    job=generate(cfg,payload,"generate-"+key)
    done=await_job(cfg,job["status_url"])
    assert done["status"]=="COMPLETED"
    return cfg,payload,key,done,cid,item

def request(cfg,method,path,body=None,key=None,token=True):
    headers={"Authorization":"Bearer "+required("API_TOKEN")} if token else {}
    if key: headers["Idempotency-Key"]=key
    return httpx.request(method,cfg.api+path,json=body,headers=headers,timeout=30)

def test_generation_idempotency_and_conflict(scenario):
    cfg,payload,key,done,_,_=scenario
    same=generate(cfg,payload,"generate-"+key)
    assert same["proposal_id"]==done["proposal_id"]
    assert request(cfg,"POST","/v1/proposals/generations",dict(payload,capacity=25),"generate-"+key).status_code==409

def test_http_negatives_and_fail_closed(scenario):
    cfg,payload,key,done,_,_=scenario
    assert request(cfg,"POST","/v1/proposals/generations",payload,key,False).status_code==401
    assert request(cfg,"POST","/v1/proposals/generations",dict(payload,capacity=0),key).status_code==422
    assert request(cfg,"POST","/v1/proposals/generations",dict(payload,mode="APPROVED"),"approved-"+key).status_code==403
    assert request(cfg,"GET",f"/v1/proposals/generations/{uuid4()}").status_code==404
    assert request(cfg,"POST",f"/v1/governance/requests/{uuid4()}/review",dict(approve=True,confirm="REVIEW_EXPLICIT_VERSION")).status_code==403

def test_contract_sql_and_storage(scenario):
    cfg,_,_,done,_,_=scenario
    from src.workbench.contract_review import fetch_payload,reconcile
    pages,offers=fetch_payload(cfg,done["proposal_id"],page_size=17)
    assert len(offers)==90
    proof=reconcile(cfg,done["proposal_id"],pages,offers)
    assert proof["sql"]["status"]=="PASS"
    assert len(proof["storage"])==3

def test_worker_trace_propagates_to_inference(scenario):
    cfg,_,_,done,_,_=scenario
    import mlflow
    mlflow.set_tracking_uri(cfg.tracking)
    assert done["trace_id"]
    trace=mlflow.get_trace(done["trace_id"])
    names={span.name for span in trace.data.spans}
    assert "worker.generation" in names and "inference.http" in names and "model.predict" in names

def test_lineage_graph_reverses_campaign(scenario):
    cfg,_,_,done,cid,item=scenario
    graph=call(cfg,"GET",f"/v1/lineage/graph?kind=campaign&external_id={cid}&limit=500")
    assert graph["total_nodes"]>0
    result=call(cfg,"GET",f"/v1/lineage?kind=run&external_id={item['mlflow_run_id']}")
    assert any(row["proposal_id"]==done["proposal_id"] for row in result["items"])

def test_campaign_control_rejects_invalid_transition(scenario):
    cfg,_,_,_,cid,_=scenario
    assert request(cfg,"POST",f"/v1/training/campaigns/{cid}/resume").status_code==409
