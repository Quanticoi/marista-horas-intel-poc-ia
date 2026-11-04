"""Actual inference with two registered versions contributing to one draft."""
import argparse
import json
from pathlib import Path
from uuid import uuid4
import numpy as np
from src.workbench.journey_config import Settings
from src.workbench.contract_review import request,invoke_demo,fetch_payload
from src.data.journey import extract,prepare,KEYS
from src.persistence.journey import compose,persist
from src.persistence.lineage import publish_manifest
from src.workbench.verification import verify_model_storage


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("first");parser.add_argument("second")
    args=parser.parse_args();cfg=Settings.load()
    frame,snapshot=extract(cfg);_,_,future=prepare(frame,snapshot)
    predictions=[];usages=[];headers=[]
    for index,execution in enumerate((args.first,args.second)):
        response=request(cfg,f"/v1/proposals/{execution}");response.raise_for_status()
        header=response.json();headers.append(header)
        inference=invoke_demo(cfg,execution)
        trace=dict(header,model_uri=f"models:/{header['model_name']}/{header['model_version']}")
        proof=verify_model_storage(trace)
        usages.append(dict(model_key=header["model_name"],registered_model_name=header["model_name"],
            model_version=header["model_version"],run_id=header["run_id"],snapshot_id=header["snapshot_id"],
            artifact_uri=header["artifact_uri"],artifact_sha256=next(p["sha256"] for p in proof if p["key"].endswith("/model.pkl")),
            inference_id=inference["inference_id"],line_keys=["/".join(str(row[k]) for k in KEYS)
                for i,row in enumerate(future.to_dict("records")) if i%2==index]))
        predictions.append(inference["predictions"])
    if usages[0]["model_version"]==usages[1]["model_version"]:
        raise ValueError("Select two distinct registered versions")
    mixed=[predictions[i%2][i] for i in range(len(future))]
    lines=compose(future,mixed)
    execution=str(uuid4());trace=dict(headers[0],model_usages=usages)
    generation=persist(cfg,execution,snapshot,trace,lines)
    repeated=persist(cfg,execution,snapshot,trace,lines)
    assert generation["execution_id"]==repeated["execution_id"]
    manifest=publish_manifest(cfg,execution)
    pages,offers=fetch_payload(cfg,execution,17)
    assert len(pages[0]["lineage"]["model_usages"])==2
    assert all(o["source_model_keys"] for o in offers)
    report=dict(test_id="AC12",status="PASS",proposal_id=execution,model_usages=usages,
                rows=len(offers),manifest=manifest,limitations="Duas versões reais; não representa validação institucional")
    Path("/reports/multi-model-proposal.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"status":"PASS","proposal_id":execution,"models":2,"rows":len(offers)}))


if __name__=="__main__":
    main()
