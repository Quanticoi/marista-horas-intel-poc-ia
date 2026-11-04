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
from src.common.tagging import SCHEMA,experiment_name,run_name,signature_hash
from src.persistence.catalog import context_for,publish

def trace_for(client,version):
    run=client.get_run(version.run_id)
    return dict(run_id=version.run_id,experiment_id=run.info.experiment_id,model_name=version.name,
        model_version=str(version.version),model_uri=f"models:/{version.name}/{version.version}",
        artifact_uri=version.source,artifact_sha256=version.tags["artifact_sha256"],metrics=run.data.metrics,
        training_execution_id=version.tags["execution_id"])


def registered_versions(client,name):
    token=None
    while True:
        page=client.search_model_versions("name = '"+name+"'",max_results=100,page_token=token)
        yield from page
        token=page.token
        if not token:
            return

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
    for version in registered_versions(client,cfg.model_name):
        if version.tags.get("operation_job_id")==job_id:
            if version.tags.get('lineage_schema_version')==SCHEMA:
                recovered=dict(version.tags,model_version=str(version.version))
                current=client.get_run(version.run_id).data.tags
                for key,value in recovered.items():
                    if key in current and current[key]!=value:
                        raise ValueError('MISMATCH: recovery shared metadata')
                    client.set_tag(version.run_id,key,value)
                client.set_model_version_tag(version.name,version.version,'model_version',str(version.version))
                version=client.get_model_version(version.name,version.version)
            result=trace_for(client,version)
            from src.workbench.verification import verify_model_storage
            result["storage_evidence"]=verify_model_storage(result)
            client.set_terminated(version.run_id,"FINISHED")
            result['catalog']=publish(client,version,result['storage_evidence'])
            attach_lineage(job,result,body["snapshot_id"])
            return result
    if job["result"].get("run_id"):
        previous=client.get_run(job["result"]["run_id"])
        if previous.info.status=="RUNNING":
            client.set_terminated(previous.info.run_id,"KILLED")
    frame,snapshot=extract(cfg,snapshot_id=body["snapshot_id"])
    context=context_for(cfg.model_name)
    if context.get('period_id'):
        frame=frame[frame.period_id.astype(str)==context['period_id']].copy()
        if frame.empty:
            raise ValueError('No historical rows for the selected academic scope')
        snapshot['dataset_sha256']=sha256(frame.to_csv(index=False).encode())
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
    cfg=replace(cfg,experiment=experiment_name(cfg.cycle))
    experiment=client.get_experiment_by_name(cfg.experiment)
    eid=experiment.experiment_id if experiment else client.create_experiment(cfg.experiment)
    if not client.get_experiment(eid).artifact_location.startswith("mlflow-artifacts:"):
        raise ValueError("Training campaigns require a proxy artifact experiment")
    wall=time.monotonic();cpu=time.process_time()
    from src.persistence.db import rows
    dataset=rows('SELECT schema_version,as_of_date FROM planning.dataset_snapshots WHERE id=:id',{'id':snapshot['id']})[0]
    label=run_name(context,body['algorithm'],time.time()*1000,job['attempt']+1,job_id)
    presentation={k:str(v) for k,v in context.items()}
    presentation.update(lineage_schema_version=SCHEMA,training_execution_id=job_id,
        campaign_display_name=body.get('campaign_display_name','Campanha DEMO'),
        experiment_id=eid,experiment_name=cfg.experiment,run_name=label,algorithm=body['algorithm'],
        dataset_schema_version=dataset['schema_version'],data_as_of_utc=str(dataset['as_of_date'])+'T00:00:00+00:00',
        query_version=snapshot['query_version'],feature_schema_hash=sha256({k:str(train[k].dtype) for k in FEATURES}),
        registered_model_name=cfg.model_name,validation_status='DEMO_CANDIDATE')
    active_span=mlflow.get_current_active_span()
    if active_span is not None:
        presentation['trace_id']=active_span.trace_id
    with mlflow.start_run(experiment_id=eid,run_name=label,tags={**identity.tags(),**presentation,
            "cycle_code":cfg.cycle,"operation_job_id":job_id,"execution_id":job_id,
            "correlation_id":job["correlation_id"],"purpose":"draft-planilha-turmas","mode":"DEMO",
            "series_scope":context.get('period_id','synthetic pooled academic rows; separate experimental identity')}) as run:
        checkpoint(job_id,{"run_id":run.info.run_id})
        mlflow.log_params({**parameters,"train_rows":len(train),"evaluation_rows":len(evaluation),"features":json.dumps(FEATURES),"target":TARGET,
            'evaluation_window':str(int(evaluation.semester_index.min()))+'..'+str(int(evaluation.semester_index.max()))})
        model.fit(train[FEATURES],train[TARGET])
        metrics=evaluate(evaluation[TARGET],model.predict(evaluation[FEATURES]))
        baseline=DummyRegressor().fit(train[FEATURES],train[TARGET])
        metrics.update({"baseline_"+k:v for k,v in evaluate(evaluation[TARGET],baseline.predict(evaluation[FEATURES])).items()})
        mlflow.log_metrics(metrics)
        sample=train[FEATURES].head(3)
        signature=infer_signature(sample,model.predict(sample))
        info=mlflow.sklearn.log_model(model,name="model",signature=signature,input_example=sample,
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
        shared={**identity.tags(),**presentation,"cycle_code":cfg.cycle,"operation_job_id":job_id,"execution_id":job_id,
            'correlation_id':job['correlation_id'],'run_id':run.info.run_id,'artifact_uri':info.model_uri,
            'artifact_sha256':digest,'model_signature_hash':signature_hash(signature)}
        version=client.create_model_version(cfg.model_name,info.model_uri,run.info.run_id,tags=shared,
            description=f"{context['model_display_name']} | {cfg.cycle} | snapshot {snapshot['id']} | {body['algorithm']} | run {run.info.run_id[:8]} | {label} | DEMO_CANDIDATE | planning.model_version_catalog")
        shared['model_version']=str(version.version)
        client.set_model_version_tag(cfg.model_name,version.version,'model_version',str(version.version))
        mlflow.set_tags(shared)
        mlflow.log_metrics({"duration_seconds":time.monotonic()-wall,"cpu_seconds":time.process_time()-cpu,
                           "peak_rss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})
        result=trace_for(client,version)
        checkpoint(job_id,result)
    from src.workbench.verification import verify_model_storage
    result["storage_evidence"]=verify_model_storage(result)
    version=client.get_model_version(cfg.model_name,result['model_version'])
    result['catalog']=publish(client,version,result['storage_evidence'])
    attach_lineage(job,result,snapshot["id"])
    return result
