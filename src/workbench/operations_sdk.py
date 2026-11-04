"""Typed notebook controls: writes only through authenticated application HTTP."""
import json
import os
import time
import tempfile
from pathlib import Path
from uuid import uuid4
import httpx
from src.common.settings import required
from src.common.lineage import utcnow,reject_sensitive
from src.workbench.sdk import source_version
from src.operations.contracts import Generation,Campaign

def call(cfg,method,path,body=None,key=None,operator=False,correlation=None):
    headers={"Authorization":"Bearer "+required("OPERATOR_TOKEN" if operator else "API_TOKEN"),
             "X-Correlation-ID":correlation or str(uuid4())}
    if key:
        headers["Idempotency-Key"]=key
    response=httpx.request(method,cfg.api+path,json=body,headers=headers,timeout=cfg.timeout)
    if response.status_code>=400:
        raise RuntimeError(f"API {method} {path}: HTTP {response.status_code}; correlation_id={response.headers.get('X-Correlation-ID','unknown')}")
    return response.json()

def generate(cfg,payload,key,correlation=None):
    body=Generation.model_validate(payload).model_dump(mode="json")
    return call(cfg,"POST","/v1/proposals/generations",body,key,correlation=correlation)

def campaign(cfg,payload,key,correlation=None):
    body=Campaign.model_validate(payload).model_dump(mode="json")
    return call(cfg,"POST","/v1/training/campaigns",body,key,correlation=correlation)

def await_job(cfg,path,timeout=600):
    deadline=time.monotonic()+timeout
    previous=None
    failures=0
    while time.monotonic()<deadline:
        try:
            value=call(cfg,"GET",path)
            failures=0
        except (httpx.TransportError,RuntimeError):
            failures+=1
            if failures>6:
                raise
            time.sleep(min(10,failures*2))
            continue
        status=value["status"]
        progress=(status,value.get("counts"))
        if progress!=previous:
            print({"status":status,"counts":value.get("counts"),"utc":utcnow()})
            previous=progress
        if status in ("COMPLETED","PARTIAL","FAILED","CANCELLED","PAUSED"):
            return value
        time.sleep(2)
    raise TimeoutError("Job remains persisted; query the same status URL to resume observation")

def write_report_file(path,content):
    """Replace atomically in the shared directory, including files owned by tools."""
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=path.parent,
                prefix="."+path.name+"-",delete=False) as stream:
            temporary=Path(stream.name)
            stream.write(content)
        temporary.chmod(0o644)
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def report(test_id,evidence,status="PASS",limitations=None,generation="v2"):
    if generation not in ('v2','v3'):
        raise ValueError('Unsupported evidence generation')
    document=dict(timestamp_utc=utcnow(),git_commit=os.getenv("CODE_VERSION","uncommitted"),
        code_version=source_version(),environment="poc",project=os.getenv("POC_PROJECT","marista"),test_id=test_id,status=status,source_type="DEMO",
        evidence=evidence,limitations=limitations or [])
    reject_sensitive(document)
    root=Path('/reports')/generation;root.mkdir(parents=True,exist_ok=True)
    if root.stat().st_uid==os.geteuid():
        root.chmod(0o777)
    path=root/(test_id+".json")
    write_report_file(path,json.dumps(document,default=str,ensure_ascii=False,indent=2))
    write_report_file(path.with_suffix(".md"),f"# {test_id}\n\n{status} — {document['timestamp_utc']}\n\nCódigo: {document['code_version']}\n\nEvidência: [{path.name}]({path.name})\n\n"+"\n".join("- "+x for x in document["limitations"]))
    return str(path)

def comparison(cfg,snapshot_id="",limit=100):
    import mlflow
    mlflow.set_tracking_uri(cfg.tracking)
    from src.common.tagging import experiment_name
    client=mlflow.MlflowClient()
    experiments=[e for e in (client.get_experiment_by_name(cfg.experiment),client.get_experiment_by_name(experiment_name(cfg.cycle))) if e]
    if not experiments:
        return []
    if snapshot_id:
        from uuid import UUID
        snapshot_id=str(UUID(snapshot_id))
    query="attributes.status = 'FINISHED'"+(" AND tags.snapshot_id = '"+snapshot_id+"'" if snapshot_id else "")
    return [{"run_id":r.info.run_id,"snapshot_id":r.data.tags.get("snapshot_id"),"model_key":r.data.tags.get("model_key"),
             "algorithm":r.data.params.get("algorithm"),"train_rows":r.data.params.get("train_rows"),
             "evaluation_rows":r.data.params.get("evaluation_rows"),"url":f"{cfg.ui}/#/experiments/{exp.experiment_id}/runs/{r.info.run_id}",
             'target':r.data.params.get('target'),'evaluation_window':r.data.params.get('evaluation_window'),
             'dataset_sha256':r.data.tags.get('dataset_sha256'),
             **r.data.metrics} for exp in experiments for r in client.search_runs([exp.experiment_id],filter_string=query,max_results=limit)]
