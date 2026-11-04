"""Read-only main-stack preservation proof, executed inside its tools container."""
import argparse,json
from pathlib import Path
import mlflow
from src.persistence.db import rows
from src.workbench.journey_config import Settings
from src.workbench.verification import verify_model_storage
from src.workbench.operations_sdk import report

parser=argparse.ArgumentParser();parser.add_argument("phase",choices=["before","after"]);args=parser.parse_args()
cfg=Settings.load();mlflow.set_tracking_uri(cfg.tracking);client=mlflow.MlflowClient()
root=Path("/reports/v2")
if args.phase=="before":
    path=root/"preservation-runtime-before.json"
    if path.exists():raise RuntimeError("Preserve original runtime baseline")
    experiments=client.search_experiments()
    runs=client.search_runs([e.experiment_id for e in experiments],max_results=10000)
    versions=list(client.search_model_versions(max_results=10000))
    data=dict(runs={r.info.run_id:dict(status=r.info.status,metrics=r.data.metrics,params=r.data.params) for r in runs if r.info.status=="FINISHED"},
        versions=[dict(name=v.name,version=v.version,run_id=v.run_id,source=v.source) for v in versions],
        proposals=rows("SELECT execution_id,payload_sha256,row_count FROM planning.proposal_generations ORDER BY execution_id"))
    path.write_text(json.dumps(data,default=str,indent=2),encoding="utf-8")
    print("PASS preservation baseline",len(data["runs"]),"runs",len(data["versions"]),"versions",len(data["proposals"]),"proposals")
else:
    data=json.loads((root/"preservation-runtime-before.json").read_text())
    for run_id,expected in data["runs"].items():
        r=client.get_run(run_id)
        assert dict(status=r.info.status,metrics=r.data.metrics,params=r.data.params)==expected
    for expected in data["versions"]:
        v=client.get_model_version(expected["name"],expected["version"])
        assert v.run_id==expected["run_id"] and v.source==expected["source"]
    for expected in data["proposals"]:
        actual=rows("SELECT payload_sha256,row_count FROM planning.proposal_generations WHERE execution_id=:id",{"id":expected["execution_id"]})[0]
        assert actual["payload_sha256"]==expected["payload_sha256"] and actual["row_count"]==expected["row_count"]
    original=json.loads((root/"inventory-before.json").read_text())["prior_execution"]
    artifact=verify_model_storage(original)
    print(report("preservation-runtime-after",dict(preserved_runs=len(data["runs"]),preserved_versions=len(data["versions"]),
        preserved_proposals=len(data["proposals"]),artifact=artifact,execution_id=original["execution_id"])))
