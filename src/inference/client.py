import httpx
from src.common.settings import required
from src.inference.contracts import InferenceRequest, InferenceResponse


def predict_remote(request: InferenceRequest):
    response = httpx.post(required("INFERENCE_URI") + "/internal/predict",
        json=request.model_dump(mode="json"),
        headers={"Authorization": "Bearer " + required("INFERENCE_TOKEN")},
        timeout=httpx.Timeout(60, connect=5))
    response.raise_for_status()
    result = InferenceResponse.model_validate(response.json())
    if (result.deployment_id != request.deployment_id or result.snapshot_id != request.snapshot_id
            or result.model_key != request.model_key):
        raise ValueError("Inference response provenance mismatch")
    return result
