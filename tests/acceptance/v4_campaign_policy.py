"""Real Workbench proof in the dedicated acceptance project only."""
import argparse
import json
import os
from pathlib import Path
from uuid import uuid4
import mlflow
from src.academic.importer import import_sources,persist
from src.simulation.academic import simulate
from src.simulation.store import save
from src.workbench.academic_campaign import execute
from src.workbench.academic_data import load
from src.data.storage import s3,bucket


def main():
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['before','after']);args=parser.parse_args()
    assert os.environ['POC_PROJECT']=='marista-correcoes-isolated'
    out=Path('/reports/v4');out.mkdir(exist_ok=True,parents=True)
    if args.phase=='before':
        imported=import_sources(Path('/reference'));persist(imported)
        snapshot=simulate(imported,seed=42,profile='baseline');save(snapshot)
        results=[]
        for _ in range(2):
            key='campaign-policy-'+str(uuid4())
            result=execute(snapshot['snapshot_id'],key,items=[dict(course_code='2248',algorithm='ridge')])
            assert result['status']=='COMPLETED'
            repeat=execute(snapshot['snapshot_id'],key,items=[dict(course_code='2248',algorithm='ridge')],resume_only=True)
            assert repeat==result
            results.append(result)
        assert len({r['experiment_id'] for r in results})==2
        assert len({r['run_id'] for r in results})==2
        assert len({r['models'][0]['model_version'] for r in results})==2
        client=mlflow.MlflowClient()
        assert all(client.get_run(r['run_id']).info.status=='FINISHED' for r in results)
        try:
            execute(snapshot['snapshot_id'],'missing-'+str(uuid4()),resume_only=True)
        except ValueError as error:
            assert 'existing campaign' in str(error)
        else:
            raise AssertionError('Unknown resume key created a campaign')
        # Exercise all versions and delete markers, not just visible S3 objects.
        storage=s3()
        for value in (b'old',b'new'):
            storage.put_object(Bucket=bucket(),Key='reset-proof/versioned',Body=value)
        storage.delete_object(Bucket=bucket(),Key='reset-proof/versioned')
        proof=dict(status='PASS',snapshot_id=snapshot['snapshot_id'],dataset_sha256=snapshot['dataset_sha256'],
                   campaigns=[{k:r[k] for k in ('campaign_id','request_key','experiment_id','experiment_name','run_id')} for r in results],
                   distinct_experiments=True,explicit_resume_unchanged=True,missing_resume_rejected=True)
        (out/'campaign-policy.json').write_text(json.dumps(proof,indent=2))
    else:
        before=json.loads((out/'campaign-policy.json').read_text())
        frame,manifest=load(before['snapshot_id'])
        assert len(frame)==285 and manifest['dataset_sha256']==before['dataset_sha256']
        # No import/reseed: training runs directly against retained SQL source.
        result=execute(before['snapshot_id'],'after-reset-'+str(uuid4()),items=[dict(course_code='2248',algorithm='ridge')])
        assert result['status']=='COMPLETED'
        proof=dict(status='PASS',snapshot_id=before['snapshot_id'],dataset_sha256=before['dataset_sha256'],
                   source_reimported=False,campaign_id=result['campaign_id'],experiment_id=result['experiment_id'])
        (out/'post-reset-training.json').write_text(json.dumps(proof,indent=2))
    print(json.dumps(proof))


if __name__=='__main__':
    main()
