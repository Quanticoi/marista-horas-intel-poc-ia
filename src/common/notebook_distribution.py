"""Publish one notebook per entry, archiving edits before a source upgrade."""
import hashlib
import json
import shutil
from pathlib import Path


def distribute(source, workspace):
    source,workspace=Path(source),Path(workspace)
    workspace.mkdir(parents=True,exist_ok=True)
    record=workspace/".distribution.json"
    prior=json.loads(record.read_text()) if record.exists() else {}
    result={}
    for path in sorted(source.glob("*.ipynb")):
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        target=workspace/path.name
        current=hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        if current is None or current==prior.get(path.name) or current==digest:
            if current!=digest:
                shutil.copyfile(path,target)
            result[path.name]=digest
        elif prior.get(path.name)==digest:
            # Same distributed release: preserve edits and outputs on restart.
            result[path.name]=digest
        else:
            backup=workspace.parent/"notebook-backups"
            backup.mkdir(parents=True,exist_ok=True)
            archived=backup/(path.stem+"."+current+".ipynb")
            if not archived.exists():
                shutil.copyfile(target,archived)
            shutil.copyfile(path,target)
            result[path.name]=digest
    record.write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result
