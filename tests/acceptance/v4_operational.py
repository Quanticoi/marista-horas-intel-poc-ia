"""Explicit DEMO operator acceptance, never an automatic startup approval."""
import argparse
import json
import os
import time
from pathlib import Path
import httpx
from src.common.lineage import sha256


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--approve-demo',action='store_true')
    args=parser.parse_args()
    if not args.approve_demo:
        raise SystemExit('Explicit --approve-demo required for POC technical review/publication')
    evidence=json.loads(Path('/reports/v4/training-cohort-evidence.json').read_text())
    client=httpx.Client(base_url=os.environ['API_URI'],timeout=120,
        headers={'Authorization':'Bearer '+os.environ['API_TOKEN']})
    operator={'Authorization':'Bearer '+os.environ['OPERATOR_TOKEN']}
    def call(method,path,**kwargs):
        response=client.request(method,path,**kwargs)
        if response.is_error:
            raise RuntimeError(f'{method} {path}: HTTP {response.status_code}, {response.text[:250]}')
        return response.json()
    selectors=[]
    for index,model in enumerate(evidence['models']):
        selector={k:model[k] for k in ('model_name','model_version')}
        selectors.append(selector)
        reviews=call('GET','/v1/governance/requests?limit=500')
        if not any(r['model_name']==model['model_name'] and r['model_version']==model['model_version'] and r['status']=='APPROVED' for r in reviews):
            pending=[r for r in reviews if r['model_name']==model['model_name'] and r['model_version']==model['model_version']
                     and r['status'] in ('RECONCILING','REQUESTED') and r['action']=='APPROVE']
            request=pending[0] if pending else call('POST','/v1/governance/requests',json=dict(**selector,requested_by='v4-demo-acceptance',
                reason='Explicit technical POC acceptance on synthetic data; not academic approval.',action='APPROVE'))
            call('POST',f"/v1/governance/requests/{request['approval_id']}/review",headers=operator,
                 json=dict(approve=True,confirm='REVIEW_EXPLICIT_VERSION'))
        call('POST',f"/v1/serving/models/{model['model_name']}/deploy",json=dict(**selector,policy='PRELOAD' if index==0 else 'LAZY'),
             headers=dict(operator,**{'Idempotency-Key':f"v4-deploy-{model['model_name']}-{model['model_version']}"}))
    payload=dict(schema_version='poc-planilha-turmas-v2',snapshot_id=evidence['snapshot_id'],cycle_code='2024-2',
        proposal_revision=1,model_selectors=selectors,requested_by='v4-demo-acceptance')
    headers={'Idempotency-Key':'v4-proposal-cohort-002'}
    job=call('POST','/v2/proposals/generations',json=payload,headers=headers)
    for _ in range(90):
        job=call('GET',job['status_url'])
        if job['status'] in ('COMPLETED','FAILED'):
            break
        time.sleep(2)
    if job['status']!='COMPLETED':
        raise RuntimeError(f"Generation {job['job_id']} status={job['status']} error={job['error_code']}")
    repeated=call('POST','/v2/proposals/generations',json=payload,headers=headers)
    assert repeated['job_id']==job['job_id']
    all_offers=[];offset=0
    while True:
        page=call('GET',job['proposal_url'],params=dict(limit=13,offset=offset))
        assert sha256({k:v for k,v in page.items() if k!='payload_sha256'})==page['payload_sha256']
        all_offers.extend(page['offers']);offset+=len(page['offers'])
        if offset==page['total_rows']:
            break
        assert page['offers']
    assert len(all_offers)==70 and len({o['offer_id'] for o in all_offers})==70
    assert sum(len(o['activities']) for o in all_offers)==107
    p164=[o for o in all_offers if o['academic']['course_code']=='2248' and o['academic']['discipline_code']=='P164']
    assert len(p164)==1
    assert sorted(a['reference_planned_students'] for a in p164[0]['activities'])==[20,21,41]
    assert p164[0]['demand']['reference_planned_students']==41
    cyber=[o for o in all_offers if o['academic']['course_code']=='2287' and o['academic']['period']==2]
    assert len(cyber)==6
    assert len({o['demand']['regular']['value'] for o in cyber})==1
    assert len({(o['demand']['dependency']['value'],o['demand']['elective']['value']) for o in cyber})>1
    assert sum(o['status']=='QUARANTINED' for o in all_offers)==12
    assert all(not o['unification']['applied'] for o in all_offers)
    audit=call('GET',f"/v2/audit/proposals/{job['proposal_id']}")
    assert audit['status']=='VERIFIED'
    filtered=call('GET',job['proposal_url'],params=dict(course_code='2248',discipline_code='P164'))
    assert filtered['total_rows']==1
    full=call('GET',job['proposal_url'])
    Path('/reports/v4/application-view-example.json').write_text(json.dumps(full,ensure_ascii=False,indent=2))
    report=dict(status='PASS',job=job,models=selectors,offers=len(all_offers),source_rows=107,
                audit=audit,idempotency='PASS',S01='PASS',S02='PASS',S03='PENDING_DATA_AND_APPROVAL')
    Path('/reports/v4/model-serving-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps({k:report[k] for k in ('status','offers','source_rows','S01','S02','S03')}))


if __name__=='__main__':
    main()
