"""Read prior evidence and verify it after rebuild without new training."""
import json
from pathlib import Path
from src.workbench.journey_config import Settings
from src.workbench.contract_review import request
from src.workbench.verification import verify_model_storage


def main():
    cfg=Settings.load()
    prior=json.loads(Path("/reports/journey-before-correcoes.json").read_text())
    current=verify_model_storage(prior)
    assert [(p["key"],p["sha256"]) for p in current]==[(p["key"],p["sha256"]) for p in prior["storage_evidence"]]
    response=request(cfg,f"/v1/proposals/{prior['execution_id']}");response.raise_for_status()
    header=response.json()
    for key in ("run_id","model_name","model_version","snapshot_id"):
        assert header[key]==prior[key]
    assert header["row_count"]==prior["persisted_rows"]
    result=dict(test_id="AC13",status="PASS",execution_id=prior["execution_id"],run_id=prior["run_id"],
                model_version=prior["model_version"],rows=header["row_count"],storage=current)
    Path("/reports/preservation-after-correcoes.json").write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="storage"}))


if __name__=="__main__":
    main()
