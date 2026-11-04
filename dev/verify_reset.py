"""Independent, read-only SDK/HTTP/SQL/S3 proof for an empty disposable POC."""
import json
from pathlib import Path
import httpx
import mlflow
from src.common.settings import required
from src.common.lineage import utcnow
from src.persistence.reset_inventory import inventory

client=mlflow.MlflowClient(tracking_uri=required("MLFLOW_TRACKING_URI"))
experiments=client.search_experiments()
assert all(experiment.name=="Default" for experiment in experiments)
assert not client.search_registered_models()
assert not client.search_runs([experiment.experiment_id for experiment in experiments])
response=httpx.get(required("API_URI")+"/v1/models",headers={"Authorization":"Bearer "+required("API_TOKEN")},timeout=15)
response.raise_for_status();assert response.json()==[]
data=inventory()
for table in ("dataset_snapshots","proposal_generations","proposal_lines","training_executions","prediction_jobs"):
    assert data["databases"]["planejamento_db"][table]["count"]==0
for table,values in data["databases"]["mlflow_db"].items():
    if "trace" in table:
        assert values["count"]==0
assert not any(q["messages"] for q in data["queues"])
assert all(o["key"]=="checks/compatibility" for o in data["objects"])
report=dict(test_id="AC19-independent",timestamp_utc=utcnow(),status="PASS",mode="empty",
            sdk_experiments=[e.name for e in experiments],sdk_models=0,sdk_runs=0,api_models=0,inventory=data)
Path("/reports/reset-independent-proof.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("PASS empty reset: SDK, API, SQL, S3 versions and queues")
