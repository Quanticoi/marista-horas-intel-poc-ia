"""Explicit C3 smoke workflow. Approval/publication remains a separate operator step."""
import json
import sys
from pathlib import Path
import httpx
from src.common.settings import required
from src.workbench.sdk import submit_dataset, test_dataset, train


def main():
    state = Path("/workspace/c3-acceptance.json")
    if sys.argv[1] == "train":
        snapshot = submit_dataset(test_dataset())
        versions = train(snapshot["id"], model_key="C1-CR1-P1")
        state.write_text(json.dumps(dict(snapshot_id=snapshot["id"], cycle_id=snapshot["cycle_id"], model=versions[0])))
        print(json.dumps(versions[0]))
    elif sys.argv[1] == "predict":
        saved = json.loads(state.read_text())
        response = httpx.post(required("API_URI")+"/v1/inference/predict", timeout=120,
            headers={"Authorization":"Bearer "+required("API_TOKEN")},
            json=dict(cycle_id=saved["cycle_id"], snapshot_id=saved["snapshot_id"],
                      model_key=saved["model"]["model_key"], requested_by="c3-acceptance"))
        response.raise_for_status()
        result = response.json()
        if isinstance(result, list):
            assert len(result) == 1
            result = result[0]
        assert result["registered_version"] == saved["model"]["version"]
        assert str(result["snapshot_id"]) == saved["snapshot_id"]
        print(json.dumps({"status":"PASS", "model":saved["model"], "prediction":result}, default=str))
    else:
        raise ValueError("Expected train or predict")


if __name__ == "__main__":
    main()
