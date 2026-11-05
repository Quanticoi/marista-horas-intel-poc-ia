"""Model fitting executes only in the Workbench image; workers never call this module."""
import os
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime,timezone
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from sklearn.dummy import DummyRegressor
import numpy as np
import psutil
import resource

from src.workbench.academic_data import FEATURES,TARGETS,prepare
from src.workbench.metrics_v4 import evaluate,profile,catalog
from src.common.tagging import signature_hash
from src.workbench.verification import verify_model_storage
from src.academic.estimator import AcademicComponents
from src.simulation.academic import digest

DEPENDENCIES=['mlflow==3.11.1','scikit-learn==1.6.1','numpy==2.2.2','pandas==2.2.3','cloudpickle==3.1.2']


def fit_model(frame,manifest,item,campaign_id,batch_id,parent_run,eid,run_id,attempt):
    if os.getenv('WORKBENCH_EXECUTOR')!='1' or not Path('/opt/conda').is_dir():
        raise RuntimeError('Training V4 requires the Jupyter Workbench container')
    client=mlflow.MlflowClient()
    train,ev,future=prepare(frame,item['course_code'])
    selected=profile(item['metric_profile'])['selected']
    if not selected:
        raise ValueError('Select a forecast metric profile for this regression')
    algorithm=item['algorithm']
    fallback=None
    if len(train)<8 or train.semester_index.nunique()<2:
        algorithm='dummy';fallback='INSUFFICIENT_TEMPORAL_HISTORY'
    model=AcademicComponents(algorithm=algorithm)
    baseline=DummyRegressor(strategy='mean')
    tags=dict(run_type='MODEL',campaign_id=campaign_id,batch_id=batch_id,parent_run_id=parent_run,
        **{'mlflow.parentRunId':parent_run},solution_id='horas-inteligentes',environment='poc',
        domain='planilha-turmas',lineage_schema_version='HI-LINEAGE/1.2',cycle_code=manifest['target'],
        model_key=item['model_key'],registered_model_name=item['model_key'],course_code=item['course_code'],
        model_family='academic-components',target_name='regular,dependency,elective',evaluation_data_class='SYNTHETIC',
        data_class='SYNTHETIC_HISTORY',snapshot_id=manifest['snapshot_id'],dataset_sha256=manifest['dataset_sha256'],
        scenario_id=manifest['scenario_id'],metric_profile=item['metric_profile'],metric_profile_version='1.0',
        cold_start_strategy='BASELINE' if fallback else 'TEMPORAL_HOLDOUT',
        data_completeness=manifest['data_completeness'],history_window=json.dumps(manifest['history_window']),
        feedback_cycles_count='0',fallback_reason=fallback or 'NONE',executor='JUPYTER_WORKBENCH',
        worker_training='false',algorithm=algorithm,validation_status='TRAINED',attempt=str(attempt),
        estimator_version='academic-components/2.0',metric_profile_sha256=digest(profile(item['metric_profile'])),
        code_version=digest({str(p.relative_to(Path('/app'))):p.read_text() for p in sorted(Path('/app/src').rglob('*.py'))}))
    wall=time.monotonic();cpu=time.process_time();process=psutil.Process()
    resources=dict(executor_pid=os.getpid(),executor_host=os.getenv('HOSTNAME','unknown'))
    with mlflow.start_run(run_id=run_id):
        mlflow.set_tags(tags)
        mlflow.log_params(dict(seed=manifest['seed'],algorithm=algorithm,requested_algorithm=item['algorithm'],
                              train_rows=len(train),evaluation_rows=len(ev),features=json.dumps(FEATURES),
                              targets=json.dumps(TARGETS),alpha=1.,max_train_cycle=str(train.cycle_code.max())))
        model.fit(train[FEATURES],train[TARGETS])
        baseline.fit(train[FEATURES],train[TARGETS])
        evaluations=[];metrics={}
        if len(ev):
            predictions=model.predict(ev[FEATURES]);base=baseline.predict(ev[FEATURES])
            for i,target in enumerate(TARGETS):
                values=evaluate(ev[target],predictions[:,i],selected)
                baseline_values=evaluate(ev[target],base[:,i],selected)
                for name,value in values.items():
                    if value['status']=='EVALUATED':
                        metrics[target+'.'+name]=value['value']
                for name,value in baseline_values.items():
                    if value['status']=='EVALUATED':
                        metrics['baseline.'+target+'.'+name]=value['value']
                evaluations.append(dict(task_type='regression',target_name=target,horizon='one-term',
                    split_id=str(ev.cycle_code.min())+'..'+str(ev.cycle_code.max()),data_class='SYNTHETIC',
                    actual=ev[target].astype(float).tolist(),predicted=predictions[:,i].tolist(),metrics=values))
        mlflow.log_metrics(metrics)
        mlflow.log_dict(catalog(),'metric_catalog.json')
        mlflow.log_dict(dict(evaluations=evaluations,status='EVALUATED' if len(ev) else 'NOT_EVALUATED',
                            reason=None if len(ev) else 'NO_TEMPORAL_HOLDOUT'),'model_errors.json')
        sample=train[FEATURES].head(3)
        signature=infer_signature(sample,model.predict(sample))
        info=mlflow.sklearn.log_model(model,name='model',signature=signature,input_example=sample,pip_requirements=DEPENDENCIES)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(mlflow.artifacts.download_artifacts(artifact_uri=info.model_uri,dst_path=directory))
            import hashlib
            artifact_sha=hashlib.sha256((path/'model.pkl').read_bytes()).hexdigest()
            artifact_bytes=(path/'model.pkl').stat().st_size
            restored=mlflow.sklearn.load_model(str(path))
            np.testing.assert_allclose(restored.predict(sample),model.predict(sample))
        from mlflow.exceptions import MlflowException
        try:
            client.create_registered_model(item['model_key'])
        except MlflowException as error:
            if error.error_code!='RESOURCE_ALREADY_EXISTS':
                raise
        version_tags=dict(tags,run_id=run_id,artifact_sha256=artifact_sha,model_signature_hash=signature_hash(signature))
        version=client.create_model_version(item['model_key'],info.model_uri,run_id,tags=version_tags)
        trace=dict(model_name=item['model_key'],model_key=item['model_key'],model_version=str(version.version),run_id=run_id,
            experiment_id=eid,model_uri=f"models:/{item['model_key']}/{version.version}",artifact_uri=info.model_uri,
            artifact_sha256=artifact_sha,signature_hash=signature_hash(signature),snapshot_id=manifest['snapshot_id'],
            dataset_sha256=manifest['dataset_sha256'],course_code=item['course_code'],targets=TARGETS,
            metric_profile=item['metric_profile'],metric_profile_version='1.0',evaluations=evaluations,
            metrics=metrics,algorithm=algorithm,validation_status='TRAINED',fallback_reason=fallback,
            trained_at=datetime.now(timezone.utc).isoformat(),future_rows=len(future),**resources)
        # Process RSS is explicitly a process measurement; concurrent models are not assigned fictitious per-model peaks.
        mlflow.log_metrics(dict(train_seconds=time.monotonic()-wall,cpu_seconds=time.process_time()-cpu,
                               process_rss_bytes=process.memory_info().rss,artifact_bytes=artifact_bytes,
                               process_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                               example_count=len(train),success=1))
        mlflow.log_dict(trace,'training_result.json')
        mlflow.set_tags(dict(model_version=str(version.version),artifact_sha256=artifact_sha,model_signature_hash=signature_hash(signature)))
    trace['storage_evidence']=verify_model_storage(trace)
    trace['validation_status']='VALIDATED' if len(ev) else 'TRAINED_NOT_EVALUATED'
    client.set_model_version_tag(trace['model_name'],trace['model_version'],'validation_status',trace['validation_status'])
    client.set_tag(run_id,'validation_status',trace['validation_status'])
    return trace
