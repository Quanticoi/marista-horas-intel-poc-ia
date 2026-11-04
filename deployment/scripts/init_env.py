"""Create missing local credentials once; never print or replace existing secrets."""
from pathlib import Path
import secrets

def initialize(root):
    target=root/".env"
    if target.exists():
        existing=target.read_text(encoding="utf-8")
        missing=[key for key in ("OPERATOR_TOKEN","INGESTION_TOKEN")
                 if not any(line.startswith(key+"=") and line.split("=",1)[1] for line in existing.splitlines())]
        if missing:
            with target.open("a",encoding="utf-8") as stream:
                stream.write("\n"+"\n".join(key+"="+secrets.token_hex(32) for key in missing)+"\n")
            print("Added missing service credentials; existing secrets preserved")
        else:
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


if __name__=="__main__":
    initialize(Path(__file__).resolve().parents[2])
