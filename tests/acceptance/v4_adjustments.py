"""Explicit selective-reset drill; exclusively marista-correcoes-isolated."""
import argparse
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--reset-isolated',action='store_true');args=parser.parse_args()
    if not args.reset_isolated:
        parser.error('Requires --reset-isolated; never operates on the main project')
    spec=importlib.util.spec_from_file_location('controller',ROOT/'deployment/scripts/reset_poc.py')
    reset=importlib.util.module_from_spec(spec);spec.loader.exec_module(reset)
    project='marista-correcoes-isolated'
    subprocess.run(['python',str(ROOT/'tests/acceptance/isolated_stack.py')],check=True)
    dc=lambda *a:reset.compose(project,*a)
    dc('up','-d','--wait','--wait-timeout','240','postgres','rustfs','rabbitmq')
    for step in ('bootstrap','migrate','buckets','migrate-mlflow'):
        dc('run','--rm','--no-deps','tools',step)
    dc('up','-d','--wait','--wait-timeout','300')
    print('Isolated services ready',flush=True)
    command=('exec','-T','jupyter','/usr/local/bin/_entrypoint.sh','python','-m','tests.acceptance.v4_campaign_policy')
    dc(*command,'before')
    print('Two campaigns, two experiments and explicit resume PASS',flush=True)
    # Quiesce before taking a stable inventory; only the dedicated project.
    dc('stop','worker','api','inference','jupyter','ingestion','dashboard','monitoramento','mlflow')
    plan=reset.preview('poc',project,'reset-experiments')
    result=reset.execute_plan(plan,'poc',project,reset.EXPERIMENT_PHRASE,True,'empty')
    assert result['status']=='RESET_PASS'
    assert result['after']['academic_source']==plan['inventory']['academic_source']
    assert not result['after']['objects']  # This disposable bucket has no backups.
    print('MLflow/storage cleared; original SQL source hashes preserved PASS',flush=True)
    dc(*command,'after')
    print('Training from retained SQL, without reimport, PASS',flush=True)
    output=ROOT/'artifacts/reports/v4-adjustments';output.mkdir(parents=True,exist_ok=True)
    source=ROOT/'.runtime/correcoes-isolated/artifacts/reports/v4'
    for name in ('campaign-policy.json','post-reset-training.json'):
        shutil.copyfile(source/name,output/name)
    proof=dict(status='PASS',timestamp_utc=datetime.now(timezone.utc).isoformat(),project=project,main_project_reset=False,
               plan_id=plan['plan_id'],source_before=plan['inventory']['academic_source'],source_after=result['after']['academic_source'],
               empty_storage_versions=len(result['after']['objects']),mlflow_after=result['after']['databases']['mlflow_db'],
               business_after=result['after']['databases']['planejamento_db'],steps=result['steps'],
               note='Empty-state proof precedes the intentional post-reset training; that training creates a new experiment/artifact.')
    (output/'selective-reset.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    main()
