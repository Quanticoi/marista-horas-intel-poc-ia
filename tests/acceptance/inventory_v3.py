"""Read-only runtime inventory. Run in tools with /repository mounted read-only."""
import importlib.metadata
import json
from pathlib import Path
import os
import hashlib
import mlflow
import requests
from src.common.lineage import utcnow
from src.data.storage import s3, bucket
from src.persistence.db import rows


def collect():
    client = mlflow.MlflowClient()
    experiments = client.search_experiments()
    runs = client.search_runs([e.experiment_id for e in experiments], max_results=10000) if experiments else []
    versions = list(client.search_model_versions(max_results=10000))
    storage = s3()
    objects = []
    for page in storage.get_paginator('list_objects_v2').paginate(Bucket=bucket()):
        for obj in page.get('Contents', []):
            objects.append({k: obj[k] for k in ('Key', 'Size', 'ETag')})
    files = {}
    root = Path('/repository')
    for folder in ('workspace/notebooks', 'notebooks'):
        for path in (root/folder).glob('*.ipynb'):
            files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    health = requests.get(os.environ['MLFLOW_TRACKING_URI']+'/health', timeout=15)
    api = requests.get(os.environ['API_URI']+'/openapi.json', timeout=15)
    api.raise_for_status()
    return dict(executed_at_utc=utcnow(), git_commit=os.environ.get('INVENTORY_HEAD'),
        dependencies={p: importlib.metadata.version(p) for p in ('mlflow','scikit-learn','pandas','numpy','sqlalchemy','boto3')},
        mlflow_health=health.status_code, api_routes=sorted(api.json()['paths']), bucket=bucket(),
        objects=objects, prefixes=sorted({o['Key'].split('/')[0] for o in objects}), notebooks=files,
        experiments=[dict(id=e.experiment_id,name=e.name) for e in experiments],
        runs={r.info.run_id:dict(status=r.info.status,metrics=r.data.metrics,params=r.data.params) for r in runs},
        versions=[dict(name=v.name,version=v.version,run_id=v.run_id,source=v.source) for v in versions],
        aliases={m.name:m.aliases for m in client.search_registered_models(max_results=1000)},
        proposals=rows('SELECT execution_id,payload_sha256,row_count FROM planning.proposal_generations ORDER BY execution_id'),
        snapshots=rows('SELECT id,sha256 FROM planning.dataset_snapshots ORDER BY id'),
        approvals=rows('SELECT * FROM planning.model_approval_requests ORDER BY approval_id'),
        migrations=rows('SELECT version_num FROM public.alembic_version', role='migration'))


if __name__ == '__main__':
    path=Path('/reports/v3/inventory-before.json')
    if path.exists():
        raise RuntimeError('Baseline already exists; never overwrite preservation evidence')
    data=collect()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.parent.chmod(0o777)
    path.write_text(json.dumps(data,default=str,indent=2),encoding='utf-8')
    print(json.dumps({k:len(data[k]) for k in ('runs','versions','proposals','objects','notebooks')}))
