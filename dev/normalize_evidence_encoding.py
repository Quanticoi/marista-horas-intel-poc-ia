"""Normalize PowerShell-redirection BOMs in report JSON; preserve JSON values."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"artifacts/reports"
count=0
for path in root.rglob("*.json"):
    if path.name in ("cleanup-2026-11-03.json","jupyter-after-rebuild-2026-11-03.json"):
        continue
    raw=path.read_bytes()
    encoding="utf-16" if raw.startswith((b"\xff\xfe",b"\xfe\xff")) else "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else None
    if encoding:
        path.write_text(raw.decode(encoding),encoding="utf-8")
        count+=1
print(f"Normalized {count} report encodings; values preserved")
