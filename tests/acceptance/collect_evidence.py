"""Archive actual isolated reports outside disposable volumes, without inventing results."""
import hashlib,json,shutil
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[2]
source=root/".runtime/correcoes-isolated/artifacts/reports/v2"
destination=root/"artifacts/reports/v2/isolated"
shutil.copytree(source,destination,dirs_exist_ok=True)
index=[]
for path in sorted(destination.rglob("*")):
    if path.is_file():
        index.append(dict(path=path.relative_to(root).as_posix(),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
for name in ("training-campaign-30.json","training-campaign-500.json","lineage-negative-tests.json","serving-after-restart.json"):
    if (source/name).exists():shutil.copyfile(source/name,destination.parent/name)
(destination.parent/"evidence-index.json").write_text(json.dumps(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
    source_project="marista-correcoes-isolated",status="ARCHIVED",files=index,
    note="Exact execution reports; early dirty-tree runs identify source content hashes, not a fabricated tested Git commit"),indent=2),encoding="utf-8")
print(f"Archived {len(index)} real isolated reports")
