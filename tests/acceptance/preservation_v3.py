"""Read-only comparison against the actual pre-V3 main-stack inventory."""
import hashlib
import json
from pathlib import Path
from inventory_v3 import collect
from src.common.lineage import canonical,utcnow
from src.workbench.sdk import source_version

before=json.loads(Path('/reports/v3/inventory-before.json').read_text(encoding='utf-8-sig'))
after=collect()
for identifier,expected in before['runs'].items():
    assert after['runs'][identifier]==expected,('run',identifier)
versions={(v['name'],v['version']):v for v in after['versions']}
for version in before['versions']:
    assert versions[(version['name'],version['version'])]==version
for name,aliases in before['aliases'].items():
    assert after['aliases'][name]==aliases,('alias',name)
for field in ('proposals','snapshots','approvals'):
    actual={canonical(row) for row in after[field]}
    assert all(canonical(row) in actual for row in before[field]),field
objects={o['Key']:o for o in after['objects']}
for item in before['objects']:
    assert objects[item['Key']]==item,('object',item['Key'])
preserved=[]
for name,digest in before['notebooks'].items():
    if not name.startswith('workspace/'):
        continue  # Source templates intentionally change; editable copies are protected below.
    candidates=[Path('/repository')/name,*Path('/repository/workspace/notebook-backups').glob(Path(name).stem+'.*.ipynb')]
    matched=[p for p in candidates if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==digest]
    assert matched,('editable notebook bytes',name)
    preserved.append(dict(name=name,sha256=digest,preserved_at=str(matched[0].relative_to('/repository'))))
proof=dict(status='AUTO_PASS',executed_at_utc=utcnow(),base_commit=before['git_commit'],code_version=source_version(),
    checks={field:len(before[field]) for field in ('runs','versions','objects','proposals','snapshots','approvals')},
    editable_notebooks=preserved,mlflow_health=after['mlflow_health'],migrations=after['migrations'])
Path('/reports/v3/preservation-after.json').write_text(json.dumps(proof,default=str,indent=2),encoding='utf-8')
print(json.dumps(proof['checks']))
