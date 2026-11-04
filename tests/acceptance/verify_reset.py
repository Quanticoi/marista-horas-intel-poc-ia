"""Read-only post-reset proof; used exclusively inside disposable tools container."""
import httpx,mlflow
from src.common.settings import required
from src.persistence.reset_inventory import inventory
from src.workbench.operations_sdk import report
from src.workbench.reset_review import inventory_view

assert required("POC_PROJECT")=="marista-correcoes-isolated"
mode=required("RESET_EXPECTED_MODE")
client=mlflow.MlflowClient()
experiments=client.search_experiments()
assert all(e.name=="Default" for e in experiments)
assert not client.search_registered_models()
assert not client.search_runs([e.experiment_id for e in experiments])
data=inventory()
for table in ("proposal_generations","proposal_lines","training_executions","prediction_jobs","operation_jobs","operation_events","training_campaigns","model_approval_requests"):
    assert data["databases"]["planejamento_db"][table]["count"]==0
assert data["databases"]["planejamento_db"]["dataset_snapshots"]["count"]==(1 if mode=="demo-ready" else 0)
for table,values in data["databases"]["mlflow_db"].items():
    if "trace" in table: assert values["count"]==0
assert not any(o["key"].startswith(("mlflow/","lineage/")) for o in data["objects"])
response=httpx.get(required("API_URI")+"/v1/training/campaigns",headers={"Authorization":"Bearer "+required("API_TOKEN")},timeout=15)
response.raise_for_status();assert response.json()==[]
print(report("reset-independent-"+mode,dict(mode=mode,models=0,runs=0,campaigns=0,inventory=inventory_view(data))))
