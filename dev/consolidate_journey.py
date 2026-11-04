"""One-time migration of the legacy duplicate, preserving exact backups."""
import hashlib
import json
import shutil
from pathlib import Path

root=Path(__file__).resolve().parents[1]
workspace=root/"workspace/notebooks"
backup=root/"workspace/notebook-backups"
backup.mkdir(parents=True,exist_ok=True)
name="01_jornada_completa_planilha_turmas.ipynb"
target=workspace/name
legacy=workspace/"01_jornada_completa_planilha_turmas.update-eeacc6e47d5c.ipynb"
source=root/"notebooks"/name
def cells(path):
    return [(c["cell_type"],"".join(c["source"])) for c in json.loads(path.read_text(encoding="utf-8"))["cells"]]
if legacy.exists():
    if cells(legacy)!=cells(source):
        raise RuntimeError("Legacy update has additional edits: review before consolidation")
    for path in (target,legacy):
        if path.exists():
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            saved=backup/(path.stem+"."+digest+".ipynb")
            shutil.copyfile(path,saved)
            assert saved.read_bytes()==path.read_bytes()
    # Both paths are explicit children of this workspace; backups verified above.
    assert target.resolve().parent==workspace.resolve()==legacy.resolve().parent
    legacy.replace(target)
    notebook=json.loads(target.read_text(encoding="utf-8"))
    for cell in notebook["cells"]:
        if cell["cell_type"]=="code":
            cell["outputs"]=[]
            cell["execution_count"]=None
    target.write_text(json.dumps(notebook,ensure_ascii=False,indent=1)+"\n",encoding="utf-8")
    record=workspace/".distribution.json"
    data=json.loads(record.read_text(encoding="utf-8"))
    data[name]=hashlib.sha256(source.read_bytes()).hexdigest()
    record.write_text(json.dumps(data,indent=2),encoding="utf-8")
assert len(list(workspace.glob("01*.ipynb")))==1
print("PASS: one canonical journey; exact backups outside notebooks")
