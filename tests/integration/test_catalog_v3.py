"""Real V3 training/storage/SQL/HTTP, no historical IDs or mocks."""
from uuid import uuid4
import json
from pathlib import Path
import pytest
from src.workbench.journey_config import Settings
from src.workbench.operations_sdk import call,campaign,await_job,generate
from src.data.journey import extract
from src.workbench.manual_validation import export_session


@pytest.fixture(scope='module')
def v3():
    cfg=Settings.load();_,snapshot=extract(cfg);session=uuid4().hex
    scopes=call(cfg,'GET','/v1/audit/scopes')[:3]
    payload=dict(snapshot_id=snapshot['id'],cycle_code=cfg.cycle,model_keys=[s['model_key'] for s in scopes],
        requested_by='pytest-v3',confirm_training=True,campaign_display_name='POC DEMO • Três períodos distintos')
    submitted=campaign(cfg,payload,'v3-'+session)
    cid=submitted['campaign_id']
    finished=await_job(cfg,f'/v1/training/campaigns/{cid}')
    assert finished['status']=='COMPLETED',finished
    items=call(cfg,'GET',f'/v1/training/campaigns/{cid}/items')
    return cfg,snapshot,session,payload,cid,items


def test_real_distinct_models_and_catalog(v3):
    cfg,snapshot,session,payload,cid,items=v3
    assert len(items)==3
    assert len({i['result']['artifact_sha256'] for i in items})==3
    for item in items:
        proof=call(cfg,'GET',f"/v1/audit/model?model_key={item['model_key']}&version={item['model_version']}")
        assert proof['status']=='VERIFIED',proof
        assert len(proof['files'])==3 and not proof['approved']
    repeated=campaign(cfg,payload,'v3-'+session)
    assert repeated['campaign_id']==cid


def test_second_version_and_reverse_proposal(v3):
    cfg,snapshot,session,payload,cid,items=v3
    second=campaign(cfg,dict(payload,model_keys=[items[0]['model_key']],alpha=7),'v3-second-'+session)
    assert await_job(cfg,f"/v1/training/campaigns/{second['campaign_id']}")['status']=='COMPLETED'
    updated=call(cfg,'GET',f"/v1/training/campaigns/{second['campaign_id']}/items")[0]
    assert int(updated['model_version'])>int(items[0]['model_version'])
    selected=[updated,*items[1:]]
    body=dict(cycle_code=cfg.cycle,snapshot_id=snapshot['id'],requested_by='pytest-v3',confirm_demo=True,
        model_selectors=[dict(model_name=i['model_key'],model_version=i['model_version']) for i in selected])
    job=generate(cfg,body,'v3-generation-'+session)
    result=await_job(cfg,job['status_url'])
    assert result['status']=='COMPLETED',result
    assert generate(cfg,body,'v3-generation-'+session)['job_id']==result['job_id']
    proof=call(cfg,'GET',f"/v1/audit/proposal/{result['proposal_id']}")
    assert proof['status']=='VERIFIED',proof
    assert len(proof['contributions'])==3
    assert proof['stored_rows']==9
    inventory=call(cfg,'GET',f'/v1/audit/inventory?campaign_id={cid}')
    exported=export_session(proof,inventory)
    path=Path('/reports/v3/scenario-latest.json');path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(dict(cfg_cycle=cfg.cycle,snapshot_id=snapshot['id'],campaign_id=cid,items=selected,
        generation_body=body,proposal_id=result['proposal_id'],session_report=exported),indent=2),encoding='utf-8')


def test_no_unknown_version_is_verified(v3):
    cfg,_,_,_,_,items=v3
    proof=call(cfg,'GET',f"/v1/audit/model?model_key={items[0]['model_key']}&version=999999")
    assert proof['status']=='NOT_FOUND'
