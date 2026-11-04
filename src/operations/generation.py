"""API-worker generation: Jupyter is only an HTTP client of this path."""
import mlflow
import httpx
from src.common.settings import required
from src.operations.config import settings
from src.operations.jobs import checkpoint,get
from src.data.journey import extract,prepare,FEATURES,KEYS
from src.persistence.journey import compose,persist
from src.persistence.lineage import publish_manifest
from src.persistence.db import rows
from src.operations.training import trace_for

def assert_approved(name,version):
    found=rows("SELECT * FROM planning.model_approval_requests WHERE model_name=:name AND model_version=:version AND status='APPROVED'",dict(name=name,version=version))
    if not found or str(mlflow.MlflowClient().get_model_version_by_alias(name,"champion").version)!=version:
        raise PermissionError("No matching authorized approval and Registry alias")

def execute(job):
    body=job["request"]; job_id=str(job["job_id"])
    cfg=settings(body["cycle_code"])
    mlflow.set_tracking_uri(cfg.tracking);mlflow.set_registry_uri(cfg.tracking)
    # Commit happened but manifest publishing failed: repair without new inference.
    if rows("SELECT execution_id FROM planning.proposal_generations WHERE execution_id=:id",{"id":job_id}):
        evidence=publish_manifest(cfg,job_id)
        return dict(proposal_id=job_id,manifest=evidence,proposal_url=f"/v1/proposals/{job_id}/application-view")
    saved=get(job_id)["result"]
    if "composition" not in saved:
        frame,snapshot=extract(cfg,snapshot_id=body["snapshot_id"])
        _,_,future=prepare(frame,snapshot)
        traces=[];usages=[];lines=[]
        for index,selector in enumerate(body["model_selectors"]):
            name=selector["model_name"];version=selector["model_version"]
            if body["mode"]=="APPROVED":
                assert_approved(name,version)
            registered=mlflow.MlflowClient().get_model_version(name,version)
            trace=trace_for(mlflow.MlflowClient(),registered)
            selected=future.iloc[index::len(body["model_selectors"])].copy()
            if selected.empty:
                raise ValueError("More model selectors than proposal rows")
            request=dict(execution_id=registered.tags["execution_id"],model_name=name,model_version=version,
                         run_id=registered.run_id,snapshot_id=body["snapshot_id"],records=selected[FEATURES].to_dict("records"),
                         correlation_id=job["correlation_id"],proposal_id=job_id)
            from src.common.tracing import trace_headers
            response=httpx.post(cfg.inference+"/internal/draft/predict",json=request,timeout=120,
                headers={"Authorization":"Bearer "+required("INFERENCE_TOKEN"),"X-Correlation-ID":job["correlation_id"],**trace_headers()})
            response.raise_for_status();prediction=response.json()
            if prediction["model_version"]!=version or prediction["run_id"]!=registered.run_id:
                raise ValueError("Inference returned another model version")
            composed=compose(selected,prediction["predictions"],body["capacity"])
            lines.extend(composed);trace["inference_id"]=prediction["inference_id"];traces.append(trace)
            usages.append(dict(model_key=name,registered_model_name=name,model_version=version,run_id=registered.run_id,
                snapshot_id=snapshot["id"],artifact_uri=registered.source,artifact_sha256=trace["artifact_sha256"],
                inference_id=prediction["inference_id"],line_keys=["/".join(str(r[k]) for k in KEYS) for r in composed]))
        trace=dict(traces[0],model_usages=usages)
        composition=dict(snapshot=snapshot,trace=trace,lines=lines)
        checkpoint(job_id,{"composition":composition})
    else:
        composition=saved["composition"]
    if body["mode"]=="APPROVED":
        for selector in body["model_selectors"]:
            assert_approved(selector["model_name"],selector["model_version"])
    persist(cfg,job_id,**composition,capacity=body["capacity"],actor="api-worker:"+job["requested_by"],correlation_id=job["correlation_id"])
    evidence=publish_manifest(cfg,job_id)
    return dict(proposal_id=job_id,manifest=evidence,proposal_url=f"/v1/proposals/{job_id}/application-view")
