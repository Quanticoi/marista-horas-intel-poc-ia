"""Collect sanitized Docker failure evidence before CI teardown."""
import json
import os
from pathlib import Path
import re
import subprocess

root=Path(__file__).resolve().parents[2]
secrets=[]
if (root/".env").exists():
    for line in (root/".env").read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key,value=line.split("=",1)
            if value and any(word in key for word in ("PASSWORD","TOKEN","SECRET","ACCESS_KEY")):
                secrets.append(value)


def clean(text):
    for secret in secrets:
        text=text.replace(secret,"[REDACTED]")
    return re.sub(r"postgresql[^\s]+", "[DATABASE_URI]", text)


report={}
for name,args in {"ps":["docker","compose","ps","--all","--format","json"],
                  "logs":["docker","compose","logs","--no-color","--tail","150","mlflow","postgres","rustfs"],
                  "health":["docker","inspect","marista-mlflow-1","--format","{{json .State.Health}}"]}.items():
    result=subprocess.run(args,capture_output=True,text=True,timeout=30)
    report[name]={"exit_code":result.returncode,"output":clean(result.stdout+result.stderr)}
folder=root/"artifacts/reports"
folder.mkdir(parents=True,exist_ok=True)
(folder/"ci-diagnostics.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("Sanitized diagnostics saved")
