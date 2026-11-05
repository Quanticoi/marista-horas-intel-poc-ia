import json
import os
from pathlib import Path
from uuid import uuid4
import httpx
import pytest
from src.persistence.db import rows
from src.workbench.academic_data import load,prepare,FEATURES
from src.api.academic_contract import ApplicationView
from src.common.lineage import sha256


@pytest.fixture(scope='module')
def context():
    path=Path('/reports/v4/model-serving-check.json')
    if not path.exists():
        pytest.skip('Run explicit DEMO operational acceptance first')
    evidence=json.loads(path.read_text())
    proof=Path('/reports/v4/application-notebook-proof.json')
    if proof.exists():
        explicit=json.loads(proof.read_text()).get('context',{}).get('proposal_id')
        if explicit:
            from src.api.academic import application_view
            document=application_view(explicit,limit=500)
            usages={u['model_name']:{k:u[k] for k in ('model_name','model_version')}
                    for offer in document['offers'] for u in offer['lineage']['model_usages']}
            evidence=dict(models=[usages[k] for k in sorted(usages)],job=dict(proposal_id=explicit,
                          proposal_url=f'/v2/proposals/{explicit}/application-view'))
    model=evidence['models'][0]
    snapshot=json.loads(Path('/reports/v4/training-cohort-evidence.json').read_text())['snapshot_id']
    frame,_=load(snapshot)
    _,_,future=prepare(frame,'2248')
    body=dict(**model,snapshot_id=snapshot,records=future[FEATURES].head(2).to_dict('records'),correlation_id=str(uuid4()))
    return evidence,body


def request(method,path,body=None,operator=False):
    response=httpx.request(method,os.environ['API_URI']+path,json=body,timeout=120,
        headers={'Authorization':'Bearer '+os.environ['OPERATOR_TOKEN' if operator else 'API_TOKEN']})
    response.raise_for_status()
    return response.json()


def predict(body):
    return httpx.post(os.environ['INFERENCE_URI']+'/internal/academic/predict',json=body,timeout=120,
        headers={'Authorization':'Bearer '+os.environ['INFERENCE_TOKEN']})


def test_real_contract_and_required_filter_fields(context):
    evidence,_=context
    payload=request('GET',evidence['job']['proposal_url'])
    assert sha256({k:v for k,v in payload.items() if k!='payload_sha256'})==payload['payload_sha256']
    ApplicationView.model_validate(payload)
    payload['offers'][0]['academic'].pop('curriculum_code')
    with pytest.raises(ValueError):
        ApplicationView.model_validate(payload)


def test_sql_dimensions_and_immutable_proposal(context):
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from src.persistence.db import engine
    assert rows('SELECT count(*) AS n FROM planning.academic_offer')[0]['n']==70
    assert rows('SELECT count(*) AS n FROM planning.offer_activity')[0]['n']==107
    proposal_id=context[0]['job']['proposal_id']
    with pytest.raises(DBAPIError),engine().begin() as con:
        con.execute(text("UPDATE planning.ai_proposal_offers_v2 SET payload='{}'::jsonb WHERE proposal_id=:id"),{'id':proposal_id})
    assert len(request('GET',context[0]['job']['proposal_url'])['offers'])==70


def test_unapproved_and_wrong_snapshot_rejected(context):
    _,body=context
    assert predict(dict(body,model_version='1')).status_code==403
    assert predict(dict(body,snapshot_id=str(uuid4()))).status_code==422


def test_revocation_blocks_warm_cache_and_restore_explicit_approval(context):
    _,body=context
    assert predict(body).status_code==200
    model={k:body[k] for k in ('model_name','model_version')}
    def review(action):
        item=request('POST','/v1/governance/requests',dict(**model,action=action,requested_by='v4-controlled-acceptance',
            reason='Controlled POC warm-cache revocation test; restoring the same explicit version.'))
        return request('POST',f"/v1/governance/requests/{item['approval_id']}/review",dict(approve=True,confirm='REVIEW_EXPLICIT_VERSION'),True)
    try:
        review('REVOKE')
        assert predict(body).status_code==403
    finally:
        review('APPROVE')
    assert predict(body).status_code==200


def test_worker_never_trains():
    from src.operations.jobs import create,process,get
    key='v4-worker-rejected-'+str(uuid4())
    job=create('training',{},key,'v4-negative-test',str(uuid4()))
    process(str(job['job_id']))
    final=get(job['job_id'])
    assert final['status']=='FAILED'
    assert final['error_code']=='LEGACY_TRAINING_DISABLED'
    assert not final['result'].get('run_id')


def test_artifact_checksum_and_signature_checked_before_loading(context):
    from src.inference.journey import load_checked
    model=context[0]['models'][0]
    with pytest.raises(ValueError,match='checksum'):
        load_checked.__wrapped__(model['model_name'],model['model_version'],'0'*64)


def test_v4_worker_trace_reaches_inference(context):
    import mlflow
    from src.operations.jobs import get
    job=get(context[0]['job']['proposal_id'])
    trace_id=job['result']['trace_id']
    trace=mlflow.get_trace(trace_id)
    names=[span.name for span in trace.data.spans]
    assert 'worker.generation' in names and 'inference.http' in names
    assert names.count('model.predict')==3
