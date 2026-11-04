"""Serving sample after host restarts inference; not 500 simultaneous loaded models."""
import json,os,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import httpx,mlflow,numpy as np
from src.workbench.journey_config import Settings
from src.common.settings import required
from src.data.journey import extract,prepare,FEATURES
from src.workbench.operations_sdk import report

def main():
    if os.getenv("POC_PROJECT")!="marista-correcoes-isolated":
        raise RuntimeError("Serving load requires isolated stack")
    cfg=Settings.load();frame,snapshot=extract(cfg);_,_,future=prepare(frame,snapshot)
    campaign=json.loads(Path("/reports/v2/training-campaign-500.json").read_text())["evidence"]
    proofs=campaign["proofs"];selected=[proofs[i] for i in (0,17,99,249,399,499)]
    mlflow.set_tracking_uri(cfg.tracking);client=mlflow.MlflowClient();payloads=[]
    for item in selected:
        version=client.get_model_version(item["model_key"],item["version"])
        payloads.append(dict(execution_id=version.tags["execution_id"],model_name=version.name,model_version=version.version,
            run_id=version.run_id,snapshot_id=snapshot["id"],records=future[FEATURES].head(5).to_dict("records")))
    headers={"Authorization":"Bearer "+required("INFERENCE_TOKEN")}
    before=httpx.get(cfg.inference+"/internal/draft/cache",headers=headers,timeout=30).json()
    def invoke(index):
        payload=payloads[index%len(payloads)];started=time.perf_counter()
        response=httpx.post(cfg.inference+"/internal/draft/predict",json=payload,headers=headers,timeout=120)
        elapsed=time.perf_counter()-started;response.raise_for_status();value=response.json()
        assert value["loaded"] and value["model_version"]==payload["model_version"] and value["run_id"]==payload["run_id"]
        return dict(seconds=elapsed,model_name=payload["model_name"],version=value["model_version"],inference_id=value["inference_id"],rows=len(value["predictions"]))
    with ThreadPoolExecutor(max_workers=2) as pool:
        observations=list(pool.map(invoke,range(60)))
    elapsed=[o["seconds"] for o in observations]
    after=httpx.get(cfg.inference+"/internal/draft/cache",headers=headers,timeout=30).json()
    print(report("serving-after-restart",dict(campaign_id=campaign["campaign"]["campaign_id"],sample_size=6,requests=60,concurrency=2,
        p50_seconds=float(np.percentile(elapsed,50)),p95_seconds=float(np.percentile(elapsed,95)),p99_seconds=float(np.percentile(elapsed,99)),
        before=before,after=after,observations=observations),limitations=["Six explicit versions sampled from 500 real training results; not 500 concurrent loaded models","Cold and warm requests mixed; six-version round robin exceeds four-entry cache"] ))

if __name__=="__main__":
    main()
