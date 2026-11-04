"""Create missing local credentials once; never print or replace existing secrets."""
from pathlib import Path
import secrets

root=Path(__file__).resolve().parents[2]
target=root/".env"
if target.exists():
    print("Existing .env preserved")
else:
    lines=[]
    for line in (root/".env.example").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#"):
            key,value=line.split("=",1)
            if not value and any(word in key for word in ("PASSWORD","TOKEN","SECRET","ACCESS_KEY")):
                line=key+"="+secrets.token_hex(32)
        lines.append(line)
    with target.open("x",encoding="utf-8") as stream:
        stream.write("\n".join(lines)+"\n")
    target.chmod(0o600)
    print("Created local .env; values not displayed")
