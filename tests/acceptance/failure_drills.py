"""Fault injection is hard-scoped to the disposable Compose project; restore in finally."""
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2]
base=["docker","compose","--env-file",".env","-f",".runtime/correcoes-isolated/compose.json"]
def run(*args):
    subprocess.run(base+list(args),cwd=root,check=True,timeout=900)
def stage(name):
    run("run","--rm","--no-deps","--entrypoint","python","tools","-m","src.workbench.v2_controls",name)
stage("controls")
try:
    run("stop","mlflow")
    stage("failed-training")
finally:
    run("up","-d","--no-deps","--wait","--wait-timeout","180","mlflow")
stage("retry")
stage("restart-start")
try:
    run("kill","-s","SIGKILL","worker")
finally:
    run("up","-d","--no-deps","--wait","--wait-timeout","180","worker")
stage("restart-check")
try:
    run("stop","postgres")
    stage("sql-down")
finally:
    run("up","-d","--no-deps","--wait","--wait-timeout","180","postgres")
print("PASS: isolated fault drills restored dependencies")
