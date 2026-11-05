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
    active={p.name for p in source.glob('*.ipynb')}
    # Archive only previously distributed files; never move a user's own notebook.
    for name in prior.keys()-active:
        if Path(name).name!=name:
            raise ValueError('Invalid notebook distribution record')
        old=workspace/name
        if old.exists():
            digest=hashlib.sha256(old.read_bytes()).hexdigest()
            backup=workspace.parent/'notebook-backups'
            backup.mkdir(parents=True,exist_ok=True)
            target=backup/(old.stem+'.'+digest+'.ipynb')
            if target.exists():
                if target.read_bytes()!=old.read_bytes():
                    raise ValueError('Notebook backup checksum collision')
                old.unlink()
            else:
                old.replace(target)
    for path in sorted(source.glob("*.ipynb")):
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        target=workspace/path.name
        current=hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
        # Keep exact prior releases as well as edits outside the visible notebook list.
        if current and current!=digest and prior.get(path.name)!=digest:
            backup=workspace.parent/"notebook-backups"
            backup.mkdir(parents=True,exist_ok=True)
            archived=backup/(path.stem+"."+current+".ipynb")
            if not archived.exists():
                shutil.copyfile(target,archived)
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
