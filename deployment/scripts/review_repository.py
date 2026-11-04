"""Read-only inventory and exact duplicate detection for maintained source files."""
import hashlib
import json
import subprocess
from collections import defaultdict
from datetime import datetime,timezone
from pathlib import Path

root=Path(__file__).resolve().parents[2]
paths=[]
for folder in ('src','tests','deployment','dev','config','sql','notebooks','docs'):
    paths.extend(p for p in (root/folder).rglob('*') if p.is_file()
                 and '__pycache__' not in p.parts and p.suffix in ('.py','.ps1','.sh','.md','.sql','.json','.yml','.yaml','.ipynb'))
groups=defaultdict(list)
inventory=[]
for path in sorted(paths):
    content=path.read_bytes();digest=hashlib.sha256(content).hexdigest()
    relative=path.relative_to(root).as_posix()
    inventory.append(dict(path=relative,bytes=len(content),sha256=digest))
    if content.strip():
        groups[digest].append(relative)
duplicates=[values for values in groups.values() if len(values)>1]
document=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
    git_commit=subprocess.check_output(['git','-c','safe.directory='+root.as_posix(),'rev-parse','HEAD'],text=True).strip(),
    environment='poc',source_type='DEMO',test_id='repository-source-inventory',status='PASS',
    files=inventory,exact_duplicates=duplicates,
    limitations=['Exact nonempty file duplicates only; semantic review is documented separately',
                 'Runtime volumes, user notebooks, generated evidence and history are outside deletion scope'])
output=root/'artifacts/reports/v2/repository-source-inventory.json'
output.write_text(json.dumps(document,indent=2),encoding='utf-8')
print(f'Inspected {len(paths)} maintained files; {len(duplicates)} exact duplicate groups')
