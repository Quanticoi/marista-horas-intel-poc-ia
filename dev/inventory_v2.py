"""Read-only starting evidence; secrets are hashed, never included."""
import hashlib
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/"artifacts/reports/v2"
out.mkdir(parents=True,exist_ok=True)
git=lambda *a:subprocess.check_output(["git","-c","safe.directory="+root.as_posix(),*a],cwd=root,text=True).strip()
protected=[root/".env",*sorted((root/"workspace/notebooks").glob("*.ipynb")),*sorted((root/"workspace/notebook-backups").glob("*.ipynb"))]
data=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),git_commit=git("rev-parse","HEAD"),environment="poc",test_id="V2-A",status="PASS",source_type="DEMO",
    branch=git("branch","--show-current"),working_tree=git("status","--short"),
    protected_sha256={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.exists()},
    prior_execution=json.loads((root/"artifacts/reports/journey-latest.json").read_text(encoding="utf-8")),
    limitations=["Inventory only; V2 implementation and acceptance pending","Working tree contains prior authorized notebook consolidation/link fixes"])
path=out/"inventory-before.json"
if path.exists():
    raise RuntimeError("Starting inventory already exists; do not replace")
path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
print("PASS starting inventory",data["git_commit"])
