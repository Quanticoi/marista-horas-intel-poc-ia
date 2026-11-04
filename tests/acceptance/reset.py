"""Explicit V2 isolated reset acceptance; never targets the main Compose project."""
import importlib.util,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("reset",root/"deployment/scripts/reset_poc.py")
reset=importlib.util.module_from_spec(spec);spec.loader.exec_module(reset)
project="marista-correcoes-isolated"
proofs=[]
def proof(mode):
    reset.compose(project,"run","--rm","--no-deps","--entrypoint","python","-e","RESET_EXPECTED_MODE="+mode,
        "-v",str(root/"tests/acceptance/verify_reset.py")+":/app/verify_reset_v2.py:ro","tools","/app/verify_reset_v2.py")
def journey():
    reset.compose(project,"exec","-T","jupyter","/usr/local/bin/_entrypoint.sh","python","-m","src.workbench.execute_journey")
    reset.compose(project,"exec","-T","jupyter","/usr/local/bin/_entrypoint.sh","python","-m","src.workbench.v2_probe")
def run(mode,reinitialize):
    reset.compose(project,"exec","-T","jupyter","/usr/local/bin/_entrypoint.sh","python","-c",
        "from src.common.notebook_distribution import distribute; distribute('/app/notebooks','/workspace/notebooks')")
    reset.compose(project,"stop","worker","api","inference","jupyter","ingestion","dashboard","monitoramento","mlflow")
    before=reset.data_inventory(project)
    plan=reset.preview("poc",project,mode)
    assert before==plan["inventory"]==reset.data_inventory(project)
    result=reset.execute_plan(plan,"poc",project,reset.PHRASE,True,reinitialize)
    assert result["status"]=="RESET_PASS"
    proof(reinitialize)
    proofs.append(dict(mode=mode,reinitialize=reinitialize,plan_id=plan["plan_id"],status=result["status"],preview_unchanged=True))
    (root/"artifacts/reports/v2/reset-isolated-proof.json").write_text(json.dumps(dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
        git_commit=subprocess.check_output(["git","-c","safe.directory="+root.as_posix(),"rev-parse","HEAD"],text=True).strip(),
        environment="poc",project=project,test_id="V2-12",status="PARTIAL",source_type="DEMO",resets=proofs),indent=2),encoding="utf-8")
    print(mode,reinitialize,"RESET_PASS",plan["plan_id"],flush=True)
run("reset-data","empty")
reset.compose(project,"run","--rm","--no-deps","tools","seed")
journey()
run("factory-reset","demo-ready")
journey()
path=root/"artifacts/reports/v2/reset-isolated-proof.json"
report=json.loads(path.read_text());report["status"]="PASS";report["post_rebuild_journeys"]="A and B executed with real training, API generation and reconciliation"
path.write_text(json.dumps(report,indent=2),encoding="utf-8")
print("PASS V2 reset and post-rebuild journeys",flush=True)
