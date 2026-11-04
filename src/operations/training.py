"""Real deterministic training jobs with Registry recovery after worker restart."""
import json
import resource
import tempfile
import time
from dataclasses import replace
from pathlib import Path
import mlflow
import mlflow.sklearn
import numpy as np
from mlflow.models import infer_signature
from sklearn.dummy import DummyRegressor
from src.common.lineage import Identity,sha256
from src.data.journey import extract,prepare,FEATURES,TARGET
from src.training.journey import estimator,evaluate,SEED
from src.operations.config import settings
from src.operations.jobs import checkpoint
from src.persistence.journey import RULE
from src.workbench.sdk import source_version

def trace_for(client,version):
    run=client.get_run(version.run_id)
    return dict(run_id=version.run_id,experiment_id=run.info.experiment_id,model_name=version.name,
        model_version=str(version.version),model_uri=f"models:/{version.name}/{version.version}",
        artifact_uri=version.source,artifact_sha256=version.tags["artifact_sha256"],metrics=run.data.metrics,
        training_execution_id=version.tags["execution_id"])

def attach_lineage(job,result,snapshot_id):
    from src.persistence.db import engine
    from src.persistence.lineage import entity,edge
    with engine().begin() as con:
        s=entity(con,"snapshot",snapshot_id,{})
        r=entity(con,"run",result["run_id"],{})
        m=entity(con,"model",result["model_name"]+"/"+result["model_version"],{"model_key":result["model_name"],"run_id":result["run_id"]})
        c=entity(con,"campaign",job["campaign_id"],{})
        edge(con,s,r,"TRAINED_ON");edge(con,r,m,"REGISTERED_AS");edge(con,c,r,"CONTRIBUTED_TO")

def execute(job):
    body=job["request"]; job_id=str(job["job_id"])
    cfg=replace(settings(body["cycle_code"]),model_name=body["model_key"])
    mlflow.set_tracking_uri(cfg.tracking);mlflow.set_registry_uri(cfg.tracking)
    client=mlflow.MlflowClient()
    # The version tag is created atomically with the version, not in a later call.
    for version in client.search_model_versions("name = '"+cfg.model_name+"'"):
        if version.tags.get("operation_job_id")==job_id:
            result=trace_for(client,version)
            from src.workbench.verification import verify_model_storage
            result["storage_evidence"]=verify_model_storage(result)
            client.set_terminated(version.run_id,"FINISHED")
            attach_lineage(job,result,body["snapshot_id"])
            return result
    if job["result"].get("run_id"):
        previous=client.get_run(job["result"]["run_id"])
        if previous.info.status=="RUNNING":
            client.set_terminated(previous.info.run_id,"KILLED")
    frame,snapshot=extract(cfg,snapshot_id=body["snapshot_id"])
    train,evaluation,future=prepare(frame,snapshot)
    model=estimator()
    if body["algorithm"]=="dummy":
        model.set_params(regression=DummyRegressor(strategy="mean"))
    else:
        model.set_params(regression__alpha=body["alpha"])
    parameters={"algorithm":body["algorithm"],"alpha":body["alpha"],"seed":SEED}
    identity=Identity(academic_cycle_id=snapshot["cycle_id"],snapshot_id=snapshot["id"],
        snapshot_sha256=snapshot["snapshot_sha256"],dataset_sha256=snapshot["dataset_sha256"],model_key=cfg.model_name,
        code_version=source_version(),config_hash=sha256(parameters),ruleset_version=RULE,
        ruleset_hash=sha256({"version":RULE,"capacity":40}),source_type="DEMO",training_campaign_id=job["campaign_id"])
    experiment=client.get_experiment_by_name(cfg.experiment)
    eid=experiment.experiment_id if experiment else client.create_experiment(cfg.experiment)
    wall=time.monotonic();cpu=time.process_time()
    with mlflow.start_run(experiment_id=eid,run_name=cfg.model_name,tags={**identity.tags(),
            "cycle_code":cfg.cycle,"operation_job_id":job_id,"execution_id":job_id,
            "correlation_id":job["correlation_id"],"purpose":"draft-planilha-turmas","mode":"DEMO",
            "series_scope":"synthetic pooled academic rows; separate experimental identity"}) as run:
        checkpoint(job_id,{"run_id":run.info.run_id})
        mlflow.log_params({**parameters,"train_rows":len(train),"evaluation_rows":len(evaluation),"features":json.dumps(FEATURES),"target":TARGET})
        model.fit(train[FEATURES],train[TARGET])
        metrics=evaluate(evaluation[TARGET],model.predict(evaluation[FEATURES]))
        baseline=DummyRegressor().fit(train[FEATURES],train[TARGET])
        metrics.update({"baseline_"+k:v for k,v in evaluate(evaluation[TARGET],baseline.predict(evaluation[FEATURES])).items()})
        mlflow.log_metrics(metrics)
        sample=train[FEATURES].head(3)
        info=mlflow.sklearn.log_model(model,name="model",signature=infer_signature(sample,model.predict(sample)),input_example=sample,
            pip_requirements=["mlflow==3.11.1","scikit-learn==1.6.1","numpy==2.2.2","pandas==2.2.3","cloudpickle==3.1.2"])
        with tempfile.TemporaryDirectory() as folder:
            downloaded=Path(mlflow.artifacts.download_artifacts(artifact_uri=info.model_uri,dst_path=folder))
            digest=sha256((downloaded/"model.pkl").read_bytes())
            restored=mlflow.sklearn.load_model(str(downloaded))
            np.testing.assert_allclose(restored.predict(sample),model.predict(sample))
        from mlflow.exceptions import MlflowException
        try:
            client.create_registered_model(cfg.model_name)
        except MlflowException as error:
            if error.error_code!="RESOURCE_ALREADY_EXISTS":
                raise
        version=client.create_model_version(cfg.model_name,info.model_uri,run.info.run_id,
            tags={**identity.tags(),"cycle_code":cfg.cycle,"operation_job_id":job_id,"execution_id":job_id,
                  "artifact_sha256":digest,"validation_status":"DEMO_CANDIDATE"})
        mlflow.log_metrics({"duration_seconds":time.monotonic()-wall,"cpu_seconds":time.process_time()-cpu,
                           "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        result=trace_for(client,version)
        checkpoint(job_id,result)
    from src.workbench.verification import verify_model_storage
    result["storage_evidence"]=verify_model_storage(result)
    attach_lineage(job,result,snapshot["id"])
    return result
