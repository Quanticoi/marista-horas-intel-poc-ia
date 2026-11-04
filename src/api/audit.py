"""Authenticated, bounded reconciliation across native IDs and immutable evidence."""
import json
from uuid import UUID
import mlflow
from fastapi import APIRouter, Depends, Query
from mlflow.exceptions import MlflowException
from botocore.exceptions import ClientError
from src.common.lineage import canonical, sha256
from src.common.tagging import assert_shared,signature_hash,SHARED
from src.persistence.catalog import inventory,scopes
from src.persistence.db import rows,engine
from src.data.storage import s3,bucket


def read_object(key):
    response=s3().get_object(Bucket=bucket(),Key=key)
    try:
        return response['Body'].read()
    finally:
        response['Body'].close()


def model_audit(name,version):
    client=mlflow.MlflowClient()
    records=rows('SELECT * FROM planning.model_version_catalog WHERE model_key=:name AND model_version=:version',dict(name=name,version=version))
    result=dict(model_key=name,model_version=version,status='NOT_FOUND',registry_accessible=False,
                registered=False,sql_approved=False,approved=False,artifact_verifiable=False,checks=[])
    import httpx
    from src.common.settings import required
    try:
        cache=httpx.get(required('INFERENCE_URI')+'/internal/draft/cache',timeout=5,
            headers={'Authorization':'Bearer '+required('INFERENCE_TOKEN')})
        cache.raise_for_status()
        result['serving']=dict(healthy=True,cached=any(v['model_key']==name and v['model_version']==version for v in cache.json().get('versions',[])),cache=cache.json()['cache'])
    except Exception:
        result['serving']=dict(healthy=False,cached=None)
    try:
        native=client.get_model_version(name,version)
        result.update(registry_accessible=True,registered=True,run_id=native.run_id,artifact_uri=native.source)
        run=client.get_run(native.run_id)
        status=assert_shared(run,native)
        approval=rows("SELECT approval_id FROM planning.model_approval_requests WHERE model_name=:name AND model_version=:version AND status='APPROVED'",dict(name=name,version=version))
        aliases=client.get_registered_model(name).aliases
        result.update(sql_approved=bool(approval),approved=bool(approval) and str(aliases.get('champion'))==version,aliases=aliases)
        if not records:
            result['status']='MISSING' if status=='VERIFIED' else 'LEGACY_PARTIAL'
            return result
        record=records[0];document=record['metadata']
        result.update(metadata=document,manifest_uri=record['manifest_uri'],manifest_sha256=record['manifest_sha256'])
        if status!='VERIFIED':
            raise ValueError('MISMATCH: catalog exists without shared tags')
        for key in SHARED:
            if str(document.get(key))!=str(native.tags.get(key)):
                raise ValueError('MISMATCH: catalog and native metadata')
        snapshot=rows('SELECT sha256,source_reference FROM planning.dataset_snapshots WHERE id=:id',{'id':record['snapshot_id']})[0]
        snapshot_raw=read_object(f"snapshots/{record['snapshot_id']}/manifest.json")
        if str(record['snapshot_id'])!=document['snapshot_id'] or sha256(snapshot_raw)!=snapshot['sha256'] or snapshot['sha256']!=document['snapshot_sha256']:
            raise ValueError('MISMATCH: SQL, catalog and snapshot manifest')
        from src.workbench.verification import verify_model_storage
        files=verify_model_storage(dict(model_name=name,model_version=version,run_id=native.run_id,model_uri=f'models:/{name}/{version}'))
        if canonical(files)!=canonical(document['files']):
            raise ValueError('MISMATCH: catalog file list')
        if next(f['sha256'] for f in files if f['key'].endswith('/model.pkl'))!=native.tags['artifact_sha256']:
            raise ValueError('MISMATCH: model checksum')
        if signature_hash(mlflow.models.get_model_info(f'models:/{name}/{version}').signature)!=native.tags['model_signature_hash']:
            raise ValueError('MISMATCH: model signature')
        prefix=f's3://{bucket()}/'
        if not record['manifest_uri'].startswith(prefix):
            raise ValueError('MISMATCH: manifest bucket')
        raw=read_object(record['manifest_uri'][len(prefix):])
        if raw!=canonical(document) or sha256(raw)!=record['manifest_sha256']:
            raise ValueError('MISMATCH: manifest bytes')
        result.update(status='VERIFIED',artifact_verifiable=True,files=files,
            checks=['native_ids','shared_tags','finished_run','signature','proxy_equals_s3','catalog_equals_manifest','snapshot_sql_equals_manifest'])
    except MlflowException as error:
        if error.error_code=='RESOURCE_DOES_NOT_EXIST':
            result.update(registry_accessible=True,status='MISSING' if records or result['registered'] else 'NOT_FOUND')
        else:
            result.update(status='MISSING',diagnostic='Registry or artifact service unavailable')
    except ClientError as error:
        result.update(status='MISSING',diagnostic='Object Store reference unavailable',error_code=error.response['Error']['Code'])
    except ValueError as error:
        result.update(status='MISSING' if str(error).startswith('MISSING:') else 'MISMATCH',
                      diagnostic='Native identity, shared tags, signature or immutable bytes could not be reconciled')
    return result


def proposal_audit(proposal_id):
    generations=rows('SELECT * FROM planning.proposal_generations WHERE execution_id=:id',{'id':proposal_id})
    if not generations:
        return dict(status='NOT_FOUND',proposal_id=str(proposal_id))
    g=generations[0]
    usages=rows('SELECT * FROM planning.proposal_model_usage WHERE proposal_id=:id ORDER BY model_key,model_version',{'id':proposal_id})
    if len(usages)>30:
        raise ValueError('Audit exceeds 30 model contributions')
    models=[model_audit(u['registered_model_name'],u['model_version']) for u in usages]
    for model in models:
        if model['status']=='NOT_FOUND':
            model.update(status='MISSING',diagnostic='SQL proposal references a version absent from Registry')
    count=rows('SELECT count(*) n FROM planning.v_proposal_lineage_readable WHERE proposal_id=:id',{'id':proposal_id})[0]['n']
    from src.api.proposal_contract import build_view
    with engine().connect() as con:
        view=build_view(con,proposal_id,g['row_count'],0)
    offers=view.model_dump(mode='json')['offers']
    line_keys={'/'.join(str(o[k]) for k in ('course_id','period_id','discipline_id')) for o in offers}
    checks=[]
    for usage in usages:
        if usage['inference_id'] is None:
            checks.append('LEGACY_PARTIAL');continue
        try:
            inference=json.loads(read_object(f"lineage/poc/planilha-turmas/inferences/{usage['inference_id']}/manifest.json"))
            checks.append('VERIFIED' if all(str(inference.get(k))==str(usage[k]) for k in
                ('inference_id','snapshot_id','run_id','registered_model_name','model_version')) else 'MISMATCH')
        except ClientError:
            checks.append('MISSING')
    assigned=[key for u in usages for key in (u['line_keys'] or [])]
    if any(u['line_keys'] is None for u in usages):
        checks.append('LEGACY_PARTIAL')
    elif set(assigned)!=line_keys or len(assigned)!=len(line_keys):
        checks.append('MISMATCH')
    else:
        checks.append('VERIFIED')
    contract=rows('SELECT payload_sha256 FROM planning.proposal_contract_evidence WHERE proposal_id=:id AND proposal_revision=1',{'id':proposal_id})
    try:
        proposal_manifest=json.loads(read_object(f'lineage/poc/planilha-turmas/proposals/{proposal_id}/revisions/1/manifest.json'))
        checks.append('VERIFIED' if contract and proposal_manifest.get('payload_sha256')==view.payload_sha256==contract[0]['payload_sha256']
            and canonical(proposal_manifest.get('lineage'))==canonical(view.lineage) else 'MISMATCH')
    except ClientError:
        checks.append('MISSING' if contract else 'LEGACY_PARTIAL')
    statuses=[m['status'] for m in models]+checks
    if count!=g['row_count'] or not usages:
        statuses.append('MISMATCH')
    status=next((s for s in ('MISMATCH','MISSING','NOT_FOUND','LEGACY_PARTIAL') if s in statuses),'VERIFIED')
    return dict(status=status,proposal_id=str(proposal_id),proposal_display_name='Planilha Turmas DEMO • '+g['status'],
        stored_rows=count,declared_rows=g['row_count'],models=models,contributions=usages,inference_checks=checks)


def router(auth):
    routes=APIRouter(dependencies=[Depends(auth)])

    @routes.get('/v1/audit/scopes')
    def academic_scopes():
        return scopes()

    @routes.get('/v1/audit/inventory')
    def catalog(model_key:str|None=Query(None,pattern=r'^[A-Za-z0-9_.-]{1,160}$'),
                run_id:str|None=Query(None,pattern=r'^[a-f0-9]{32}$'),snapshot_id:UUID|None=None,
                campaign_id:UUID|None=None,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0,le=100000)):
        return inventory(model_key,run_id,snapshot_id,campaign_id,limit,offset)

    @routes.get('/v1/audit/model')
    def model(model_key:str=Query(pattern=r'^[A-Za-z0-9_.-]{1,160}$'),version:str=Query(pattern=r'^[1-9][0-9]{0,11}$')):
        return model_audit(model_key,version)

    @routes.get('/v1/audit/proposal/{proposal_id}')
    def proposal(proposal_id:UUID):
        return proposal_audit(proposal_id)
    return routes
