"""Smoke the implemented catalog in fresh kernels; opt-in writes remain disabled."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from src.common.lineage import utcnow


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--proposal-id",required=True)
    parser.add_argument("--reset-plan-id",required=True)
    args=parser.parse_args()
    results=[]
    for notebook in sorted(Path("/app/notebooks").glob("*.ipynb")):
        if notebook.name.startswith("01_"):
            continue  # Already exercised separately; avoid another training.
        process=subprocess.run(["python","-m","src.workbench.execute_notebook",notebook.name,
            "--proposal-id",args.proposal_id,"--reset-plan-id",args.reset_plan_id],capture_output=True,text=True,timeout=300)
        results.append(dict(notebook=notebook.name,status="PASS" if process.returncode==0 else "FAIL",exit_code=process.returncode))
        print(results[-1])
        if process.returncode:
            raise RuntimeError("Notebook failed; inspect its executed copy: "+notebook.name)
    Path("/reports/catalog-smoke.json").write_text(json.dumps(dict(timestamp_utc=utcnow(),results=results,
        limitations="04 training opt-in disabled;05 scheduler NOT_IMPLEMENTED;07 no promotion;09 preview only"),indent=2))


if __name__=="__main__":
    main()
