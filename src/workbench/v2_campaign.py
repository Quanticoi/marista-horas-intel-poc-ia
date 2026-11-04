"""Bounded real training campaign; counts are verified against actual Registry runs."""
import argparse
import json
import time
from pathlib import Path
from uuid import uuid4
import mlflow
from src.workbench.journey_config import Settings
from src.workbench.operations_sdk import campaign,await_job,call,report
from src.data.journey import extract

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--count",type=int,choices=[30,500],required=True)
    parser.add_argument("--campaign-id")
    args=parser.parse_args();cfg=Settings.load();_,snapshot=extract(cfg)
    correlation=str(uuid4());keys=[f"hi.demo.scale{args.count}.{correlation[:8]}.{i:03}" for i in range(args.count)]
    wall=time.monotonic()
    if args.campaign_id:
        from uuid import UUID
        cid=str(UUID(args.campaign_id))
    else:
        submitted=campaign(cfg,dict(snapshot_id=snapshot["id"],cycle_code=cfg.cycle,model_keys=keys,
            requested_by="isolated-scale-test",confirm_training=True,max_parallel_jobs=2),correlation,correlation)
        cid=submitted["campaign_id"]
    report(f"training-campaign-{args.count}-started",dict(campaign_id=cid,requested_count=args.count),"PARTIAL")
    completed=await_job(cfg,f"/v1/training/campaigns/{cid}",timeout=7200)
    items=call(cfg,"GET",f"/v1/training/campaigns/{cid}/items?limit=500")
    mlflow.set_tracking_uri(cfg.tracking);client=mlflow.MlflowClient()
    proofs=[]
    for item in items:
        if item["status"]!="COMPLETED":
            continue
        version=client.get_model_version(item["registered_model_name"],item["model_version"])
        run=client.get_run(item["mlflow_run_id"])
        assert run.info.status=="FINISHED" and version.run_id==run.info.run_id
        assert run.data.tags["training_campaign_id"]==cid
        assert "mae" in run.data.metrics and "rmse" in run.data.metrics
        assert version.tags["artifact_sha256"]==item["result"]["artifact_sha256"]
        assert len(item["result"]["storage_evidence"])==3
        proofs.append(dict(model_key=item["model_key"],version=item["model_version"],run_id=run.info.run_id,
            artifact_sha256=version.tags["artifact_sha256"],metrics=run.data.metrics,attempt=item["attempt"],
            artifact_uri=version.source,storage_evidence=item["result"]["storage_evidence"]))
    status="PASS" if completed["status"]=="COMPLETED" and len(proofs)==args.count else "FAIL"
    print(report(f"training-campaign-{args.count}",dict(campaign=completed,actual_trained=len(proofs),
        observation_seconds=time.monotonic()-wall,cpu_seconds=sum(p["metrics"].get("cpu_seconds",0) for p in proofs),
        peak_worker_rss_kib=max((p["metrics"].get("peak_rss_kib",0) for p in proofs),default=0),
        concurrency_limit=2,proofs=proofs),status,["Separate synthetic experimental identities trained on the same pooled DEMO snapshot; not institutional model quality","Two worker processes, no automatic serving or promotion"]))
    assert status=="PASS"

if __name__=="__main__":
    main()
