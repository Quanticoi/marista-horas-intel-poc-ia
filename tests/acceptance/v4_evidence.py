"""Collect current, explicit V4 context and cross-store proof; never select latest."""
import json
import os
from pathlib import Path
from datetime import datetime,timezone
import httpx
import mlflow
from src.persistence.db import rows
from src.serving.audit import proposal
from src.common.lineage import sha256


def main():
    root=Path('/reports/v4')
    proof=json.loads((root/'application-notebook-proof.json').read_text())
    context=proof['context'];pid=context['proposal_id']
    result=rows('SELECT result FROM planning.workbench_campaigns WHERE campaign_id=:id',{'id':context['campaign_id']})[0]['result']
    with httpx.Client(base_url=os.environ['API_URI'],headers={'Authorization':'Bearer '+os.environ['API_TOKEN']},timeout=120) as client:
        response=client.get(f'/v2/proposals/{pid}/application-view');response.raise_for_status();view=response.json()
        catalog=client.get('/v1/serving/models');catalog.raise_for_status()
    audit=proposal(pid)
    job=rows('SELECT result FROM planning.operation_jobs WHERE job_id=:id',{'id':pid})[0]['result']
    trace=mlflow.get_trace(job['trace_id'])
    names=[s.name for s in trace.data.spans]
    assert names.count('model.predict')==3 and 'inference.http' in names
    client=mlflow.MlflowClient()
    for model in result['models']:
        assert client.get_run(model['run_id']).info.status=='FINISHED'
        for evaluation in model['evaluations']:
            assert evaluation['observation_grain'] in ('cohort-cycle','offer-cycle')
    for name,document in [('training-final-evidence.json',result),('mlflow-campaign-summary.json',result),
        ('application-view-final.json',view),('final-lineage.json',audit),('serving-catalog-final.json',catalog.json())]:
        (root/name).write_text(json.dumps(document,ensure_ascii=False,indent=2))
    from src.workbench.metrics_v4 import catalog as metrics
    (root/'metric-catalog.json').write_text(json.dumps(metrics(),ensure_ascii=False,indent=2))
    document=dict(status='PASS',timestamp_utc=datetime.now(timezone.utc).isoformat(),context=context,
        source='REFERENCE_STRUCTURE_AND_SYNTHETIC_HISTORY',seed=42,trace_id=job['trace_id'],spans=names,
        offers=view['total_rows'],source_rows=sum(len(o['activities']) for o in view['offers']),
        payload_sha256=view['payload_sha256'],proposal_sha256=view['proposal_sha256'],
        source_code_sha256=sha256({str(p.relative_to('/app')):sha256(p.read_bytes()) for p in sorted(Path('/app/src').rglob('*.py'))}),
        manual='MANUAL_NOT_CHECKED',remote_ci='NOT_EXECUTED',limitations=['No academic approval, official capacity or PRIME integration.'])
    (root/'final-proof.json').write_text(json.dumps(document,ensure_ascii=False,indent=2))
    print(json.dumps(dict(status='PASS',proposal_id=pid,offers=document['offers'],source_rows=document['source_rows'],trace_id=job['trace_id'])))


if __name__=='__main__':
    main()
