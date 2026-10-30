"""Stable internal address for one dedicated API per registered model name."""
import hashlib
import os
import httpx
from src.common.settings import required
from src.inference.contracts import InferenceResponse


def service_name(model_key):
    return "model-" + hashlib.sha256(model_key.encode()).hexdigest()[:16]


def route(request):
    suffix = os.getenv("MODEL_DNS_SUFFIX", "")
    url = f"http://{service_name(request.model_key)}{suffix}:8001/internal/predict"
    response = httpx.post(url, json=request.model_dump(mode="json"), timeout=httpx.Timeout(60, connect=5),
        headers={"Authorization":"Bearer " + required("INFERENCE_TOKEN")})
    response.raise_for_status()
    result = InferenceResponse.model_validate(response.json())
    if (result.model_key != request.model_key or result.deployment_id != request.deployment_id
            or result.snapshot_id != request.snapshot_id):
        raise ValueError("Model service provenance mismatch")
    return result
