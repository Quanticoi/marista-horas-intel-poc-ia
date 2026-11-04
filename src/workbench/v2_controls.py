"""Real pause/resume/cancel and retry checkpoints, coordinated by host fault drills."""
import argparse,os,json,time
from pathlib import Path
from uuid import uuid4
import httpx
from src.common.settings import required
from src.workbench.journey_config import Settings
from src.workbench.operations_sdk import call,campaign,await_job,report
from src.data.journey import extract

def main():
    if os.getenv("POC_PROJECT")!="marista-correcoes-isolated":
        raise RuntimeError("Disposable project required")
    parser=argparse.ArgumentParser();parser.add_argument("stage",choices=["controls","failed-training","retry","sql-down"]);args=parser.parse_args()
    cfg=Settings.load();root=Path("/reports/v2")
    if args.stage=="sql-down":
        response=httpx.get(cfg.api+"/v1/training/campaigns",headers={"Authorization":"Bearer "+required("API_TOKEN")},timeout=30)
        assert response.status_code==503
        print(report("sql-unavailable",{"http_status":503}));return
    if args.stage=="retry":
        previous=json.loads((root/"retry-training-failed.json").read_text())["evidence"]
        cid=previous["campaign_id"]
        call(cfg,"POST",f"/v1/training/campaigns/{cid}/retry-failed")
        state=await_job(cfg,f"/v1/training/campaigns/{cid}")
        assert state["status"]=="COMPLETED"
        items=call(cfg,"GET",f"/v1/training/campaigns/{cid}/items")
        print(report("retry-training-recovered",dict(campaign_id=cid,state=state,items=items)));return
    _,snapshot=extract(cfg);stamp=uuid4().hex[:8]
    count=30 if args.stage=="controls" else 1
    submitted=campaign(cfg,dict(snapshot_id=snapshot["id"],cycle_code=cfg.cycle,
        model_keys=[f"hi.demo.controls.{stamp}.{i}" for i in range(count)],max_attempts=1,
        requested_by="isolated-controls",confirm_training=True),str(uuid4()))
    cid=submitted["campaign_id"];url=f"/v1/training/campaigns/{cid}"
    if args.stage=="failed-training":
        state=await_job(cfg,url,timeout=600);assert state["status"]=="FAILED"
        print(report("retry-training-failed",dict(campaign_id=cid,state=state,reason="Host deliberately stopped isolated MLflow")));return
    call(cfg,"POST",url+"/pause");paused=await_job(cfg,url);assert paused["status"]=="PAUSED"
    time.sleep(3);still=call(cfg,"GET",url);assert still["counts"]==paused["counts"]
    call(cfg,"POST",url+"/resume")
    time.sleep(2)
    call(cfg,"POST",url+"/cancel");cancelled=await_job(cfg,url)
    assert cancelled["status"]=="CANCELLED" and cancelled["counts"].get("CANCELLED",0)>0
    print(report("campaign-controls",dict(campaign_id=cid,paused=paused,stable_pause=still,cancelled=cancelled)))

if __name__=="__main__":
    main()
