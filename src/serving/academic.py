"""V4 eligibility reuses the existing RECONCILING approval/Registry policy."""
import json
from datetime import datetime,timezone,timedelta
import mlflow
from sqlalchemy import text
from src.persistence.db import rows,engine,audit
from src.operations.generation import assert_approved
from src.workbench.verification import verify_model_storage
from src.common.tagging import signature_hash
from src.simulation.academic import digest


def scientific_result(name,version):
    found=rows("""SELECT result FROM planning.workbench_models WHERE state='COMPLETED'
        AND model_key=:name AND result->>'model_version'=:version""",dict(name=name,version=version))
    if len(found)!=1:
        raise ValueError('Unique completed Workbench model checkpoint required')
    return found[0]['result']


def validate(name,version):
    result=scientific_result(name,version)
    client=mlflow.MlflowClient();registered=client.get_model_version(name,version)
    run=client.get_run(registered.run_id)
    if run.info.status!='FINISHED' or result['run_id']!=registered.run_id or result['validation_status']!='VALIDATED':
        raise ValueError('Model not scientifically validated in Workbench')
    if registered.tags.get('data_class')!='SYNTHETIC_HISTORY' or not result['evaluations']:
        raise ValueError('Only traceable evaluated POC models are eligible')
    from src.workbench.academic_data import load
    _,snapshot=load(result['snapshot_id'])
    if snapshot['dataset_sha256']!=result['dataset_sha256']:
        raise ValueError('Model snapshot integrity mismatch')
    for field in ('snapshot_id','dataset_sha256','artifact_sha256','course_code'):
        if registered.tags.get(field)!=str(result[field]) or run.data.tags.get(field)!=str(result[field]):
            raise ValueError('Model metadata mismatch: '+field)
    stored=verify_model_storage(result)
    if next(f['sha256'] for f in stored if f['key'].endswith('/model.pkl'))!=result['artifact_sha256']:
        raise ValueError('Model binary mismatch')
    info=mlflow.models.get_model_info(result['model_uri'])
    if signature_hash(info.signature)!=result['signature_hash']:
        raise ValueError('Model signature mismatch')
    return result


def deploy(name,version,policy,key,actor):
    if policy not in ('LAZY','PRELOAD') or not key:
        raise ValueError('Explicit load policy and idempotency key required')
    assert_approved(name,version)
    result=validate(name,version)
    body=dict(model_name=name,model_version=version,policy=policy,environment='poc')
    with engine().begin() as con:
        con.execute(text('SELECT pg_advisory_xact_lock(hashtext(:key))'),{'key':'deploy:'+name})
        prior=con.execute(text('SELECT * FROM planning.academic_deployments WHERE request_key=:key'),{'key':key}).mappings().first()
        if prior:
            if prior['request_hash']!=digest(body):
                raise ValueError('Deployment idempotency conflict')
            return dict(prior)
        existing=con.execute(text('SELECT 1 FROM planning.academic_deployments WHERE model_name=:n AND model_version=:v'),{'n':name,'v':version}).first()
        if existing:
            raise ValueError('Version already deployed; inspect its explicit policy/expiry')
        expires=datetime.now(timezone.utc)+timedelta(days=30)
        con.execute(text("""INSERT INTO planning.academic_deployments
            (model_name,model_version,run_id,snapshot_id,request_key,request_hash,policy,status,environment,metadata,expires_at)
            VALUES (:n,:v,:run,:snapshot,:key,:hash,:policy,'DEPLOYED','poc',CAST(:metadata AS jsonb),:expires)"""),
            dict(n=name,v=version,run=result['run_id'],snapshot=result['snapshot_id'],key=key,hash=digest(body),
                 policy=policy,metadata=json.dumps(result),expires=expires))
        audit(con,actor,'V4_MODEL_DEPLOYED','model',name+'/'+version,key,body)
    return dict(body,status='DEPLOYED',expires_at=expires.isoformat())


def eligible(name,version,snapshot_id=None,role='app'):
    found=rows("""SELECT * FROM planning.academic_deployments WHERE model_name=:n AND model_version=:v
        AND status='DEPLOYED' AND environment='poc' AND expires_at>now()""",{'n':name,'v':version},role=role)
    if not found:
        raise PermissionError('Model not deployed, expired or unavailable')
    assert_approved(name,version,role=role)  # Always runs, even with a warm model cache.
    deployment=found[0]
    if snapshot_id and str(deployment['snapshot_id'])!=str(snapshot_id):
        raise ValueError('Snapshot does not match explicitly deployed model')
    registered=mlflow.MlflowClient().get_model_version(name,version)
    if registered.run_id!=deployment['run_id'] or registered.tags.get('artifact_sha256')!=deployment['metadata']['artifact_sha256']:
        raise ValueError('Deployment/Registry mismatch')
    if mlflow.MlflowClient().get_run(registered.run_id).info.status!='FINISHED':
        raise ValueError('Run is not FINISHED')
    return deployment
