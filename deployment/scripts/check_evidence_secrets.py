"""Check evidence for configured secret values without revealing matches."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
values=[]
for line in (root/".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        key,value=line.split("=",1)
        if len(value)>8 and any(term in key for term in ("PASSWORD","TOKEN","SECRET","ACCESS_KEY")):
            values.append(value.encode())
failures=[]
for folder in ("notebooks","artifacts/reports","docs"):
    for path in (root/folder).rglob("*"):
        if path.is_file() and path.suffix in (".json",".md",".ipynb",".xml",".txt"):
            content=path.read_bytes()
            if any(value in content for value in values):
                failures.append(str(path.relative_to(root)))
if failures:
    raise SystemExit("Secret value found in evidence files: "+", ".join(failures))
print("PASS: no configured secret values in notebooks, docs or evidence")
