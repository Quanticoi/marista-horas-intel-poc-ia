"""Two explicit versions generate one proposal through the operational API."""
import json
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlencode
from src.workbench.journey_config import Settings
from src.workbench.operations_sdk import generate,await_job,call,report
from src.workbench.contract_review import fetch_payload,reconcile


def main():
    cfg=Settings.load()
    journey=json.loads(Path('/reports/journey-latest.json').read_text())
    probe=json.loads(Path('/reports/v2/probe-complete.json').read_text())['evidence']
    usage=probe['pages'][0]['lineage']['model_usages'][0]
    selectors=[dict(model_name=journey['model_name'],model_version=journey['model_version']),
               dict(model_name=usage['registered_model_name'],model_version=usage['model_version'])]
    key=str(uuid4())
    submitted=generate(cfg,dict(cycle_code=cfg.cycle,snapshot_id=journey['snapshot_id'],
        model_selectors=selectors,requested_by='lineage-nn-proof',confirm_demo=True),key,key)
    job=await_job(cfg,submitted['status_url'])
    assert job['status']=='COMPLETED',job
    pages,offers=fetch_payload(cfg,job['proposal_id'])
    evidence=reconcile(cfg,job['proposal_id'],pages,offers)
    usages=pages[0]['lineage']['model_usages']
    assert len(usages)==2
    first,second=[set(u['line_keys']) for u in usages]
    assert first.isdisjoint(second) and len(first|second)==len(offers)==90
    reverse=[]
    for item in usages:
        query=urlencode(dict(kind='run',external_id=item['run_id'],limit=500))
        found=call(cfg,'GET','/v1/lineage?'+query)
        assert any(str(row['proposal_id'])==job['proposal_id'] for row in found['items'])
        reverse.append(found)
    assert generate(cfg,dict(cycle_code=cfg.cycle,snapshot_id=journey['snapshot_id'],
        model_selectors=selectors,requested_by='lineage-nn-proof',confirm_demo=True),key,key)['generation_job_id']==submitted['generation_job_id']
    print(report('lineage-cross-system',dict(proposal_id=job['proposal_id'],request_models=selectors,
        model_usages=usages,rows_per_model=[len(first),len(second)],reconciliation=evidence,
        reverse_lookup=reverse,idempotency='PASS'),limitations=['Deterministic alternating DEMO rows; not an academic model allocation rule']))


if __name__=='__main__':
    main()
