"""Execute every notebook, including opt-in writes, in fresh isolated kernels."""
import json
import os
import shutil
import subprocess
import argparse
from pathlib import Path
from uuid import uuid4
from src.workbench.operations_sdk import report
from src.workbench.journey_config import Settings
from src.data.journey import extract

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--resume-governance",action="store_true");args=parser.parse_args()
    if os.getenv("POC_ISOLATED_TESTS")!="1":
        raise RuntimeError("Opt-in suite requires explicitly isolated stack")
    cfg=Settings.load();_,snapshot=extract(cfg);prefix=uuid4().hex[:8]
    results=[];root=Path("/reports/v2/notebooks");root.mkdir(parents=True,exist_ok=True)
    base=dict(V2_SNAPSHOT_ID=snapshot["id"],V2_REQUEST_KEY="notebooks-"+prefix,
        V2_MODEL_NAME="hi.demo.notebook."+prefix,V2_CONFIRMATION="EXECUTE_DEMO",V2_EXECUTE_WRITE="true")
    def run(number,case,parameters=None):
        source=next(Path("/app/notebooks").glob(f"{number:02}_*.ipynb"))
        env={k:v for k,v in os.environ.items() if not k.startswith("V2_")}
        env.update({k:str(v) for k,v in (parameters or {}).items()})
        process=subprocess.run(["python","-m","src.workbench.execute_notebook",source.name],env=env,capture_output=True,text=True,timeout=1200)
        executed=Path("/reports")/(source.stem+".executed.ipynb")
        if executed.exists(): shutil.copyfile(executed,root/(case+".ipynb"))
        results.append(dict(notebook=source.name,case=case,status="PASS" if process.returncode==0 else "FAIL",evidence="notebooks/"+case+".ipynb"))
        print(results[-1],flush=True)
        report("notebook-suite",results,"PARTIAL" if process.returncode==0 else "FAIL")
        if process.returncode:
            raise RuntimeError("Notebook failed: "+case+"; inspect executed evidence")
        saved=Path("/reports/v2")/(source.stem+".json")
        return json.loads(saved.read_text())["evidence"] if saved.exists() else {}
    if args.resume_governance:
        saved=lambda name:json.loads((Path("/reports/v2")/(name+".json")).read_text())["evidence"]
        results.extend(r for r in saved("notebook-suite") if r["status"]=="PASS")
        single=saved("04_treinamento_individual");proposal=saved("02_teste_inferencia_planilha_turmas")["proposal_id"]
        request=saved("07_registry_governanca");version=request["review"]["model_version"]
        base["V2_MODEL_NAME"]=request["review"]["model_name"]
    else:
        run(0,"00-read")
        run(1,"01-legacy")
        run(3,"03-read",base)
        single=run(4,"04-train",base)
        same=run(4,"04-repeat-same-key",base)
        assert single["items"][0]["model_version"]==same["items"][0]["model_version"]
        version=single["items"][0]["model_version"]
        generation=run(2,"02-generate",dict(base,V2_REQUEST_KEY="proposal-"+prefix,V2_MODE="GENERATE_AND_VALIDATE",V2_MODEL_VERSION=version))
        proposal=generation["proposal_id"]
        run(2,"02-read",dict(V2_PROPOSAL_ID=proposal))
        run(5,"05-campaign-30",dict(base,V2_REQUEST_KEY="campaign-"+prefix,V2_CAMPAIGN_ACTION="create",V2_MODEL_COUNT="30"))
        run(6,"06-compare",dict(V2_SNAPSHOT_ID=snapshot["id"]))
        run(7,"07-read",dict(base,V2_EXECUTE_WRITE="false",V2_MODEL_VERSION=version))
        request=run(7,"07-request",dict(base,V2_MODEL_VERSION=version,V2_GOVERNANCE_ACTION="request",V2_REASON="Isolated notebook approval acceptance"))
    approved=run(7,"07-approve",dict(base,V2_MODEL_VERSION=version,V2_GOVERNANCE_ACTION="approve",V2_APPROVAL_ID=request["review"]["approval_id"]))
    assert approved["review"]["status"]=="APPROVED"
    run(8,"08-proposal",dict(V2_PROPOSAL_ID=proposal))
    for kind,external in (("campaign",single["campaign"]["campaign_id"]),("run",single["items"][0]["mlflow_run_id"]),("snapshot",snapshot["id"]),("model",base["V2_MODEL_NAME"])):
        run(8,"08-"+kind,dict(V2_LINEAGE_KIND=kind,V2_EXTERNAL_ID=external,V2_MODEL_VERSION=version))
    run(9,"09-preview")
    report("notebook-suite",results,"PASS",["Reset notebook is read-only; destructive controller acceptance is a separate isolated test","Governance approval is a technical DEMO approval, not academic publication"])

if __name__=="__main__":
    main()
