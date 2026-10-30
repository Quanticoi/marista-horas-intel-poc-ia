import io
import json
import uuid
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from src.inference import runtime
from src.inference.contracts import InferenceRequest
from src.inference.main import app


def request():
    return InferenceRequest(deployment_id=uuid.uuid4(),snapshot_id=uuid.uuid4(),
        model_key='C1-CR1-P1',target_year=2026,target_semester=1)


def test_internal_endpoint_requires_separate_token(monkeypatch):
    monkeypatch.setenv('INFERENCE_TOKEN','internal-test-token')
    client=TestClient(app)
    assert client.post('/internal/predict',json=request().model_dump(mode='json')).status_code==401
    assert client.post('/internal/predict',headers={'Authorization':'Bearer public-api-token'},
        json=request().model_dump(mode='json')).status_code==401


def test_unapproved_version_never_fetches_object(monkeypatch):
    monkeypatch.setattr(runtime,'rows',lambda *args,**kwargs: [])
    def forbidden(*args):
        pytest.fail('Unapproved model must not be downloaded')
    monkeypatch.setattr(runtime,'artifact',forbidden)
    with pytest.raises(ValueError,match='Approved deployment'):
        runtime.infer(request())


def test_binary_executes_with_provenance_without_refit(monkeypatch):
    body=request()
    uri='s3://pucpr-poc/mlflow/run/model'
    info=dict(schema_version='2.0',fallback=True,model_key=body.model_key,
              snapshot_id=str(body.snapshot_id),run_id='run',code_version='code',dataset_sha256='dataset')
    row=dict(model_key=body.model_key,registered_version='2',artifact_uri=uri,
             artifact_sha256='sha',mlflow_run_id='run',code_version='code',dataset_sha256='dataset')
    reads=[]
    def load(*args):
        reads.append(args)
        return SimpleNamespace(predict=lambda frame: [40.0]),info
    monkeypatch.setattr(runtime,'load_bundle',load)
    monkeypatch.setattr(runtime,'rows',lambda *args,**kwargs: [row])
    monkeypatch.setattr(runtime,'MlflowClient',lambda: SimpleNamespace(get_model_version_by_alias=lambda *args:
        SimpleNamespace(version='2',source=uri,run_id='run',tags={'bundle_sha256':'sha'})))
    runtime.artifact.cache_clear()
    try:
        result=runtime.infer(body)
        assert result.forecast_raw==40 and result.mlflow_run_id=='run'
        runtime.infer(body)
        assert len(reads)==1
        row['artifact_sha256']='tampered'
        with pytest.raises(ValueError,match='provenance changed'):
            runtime.infer(body)
    finally:
        runtime.artifact.cache_clear()


def test_loader_rejects_non_poc_storage():
    from src.mlops.artifacts import object_prefix
    with pytest.raises(ValueError,match='approved object storage'):
        object_prefix('https://example.invalid/model')


def test_client_rejects_mismatched_deployment(monkeypatch):
    from src.inference import client
    body=request()
    monkeypatch.setenv('INFERENCE_URI','http://inference:8001')
    monkeypatch.setenv('INFERENCE_TOKEN','internal-test-token')
    payload=dict(body.model_dump(mode='json'),deployment_id=str(uuid.uuid4()))
    payload.pop('target_year'); payload.pop('target_semester')
    payload.update(registered_version='1',forecast_raw=12,is_fallback=True)
    monkeypatch.setattr(client.httpx,'post',lambda *args,**kwargs: SimpleNamespace(
        raise_for_status=lambda:None,json=lambda:payload))
    with pytest.raises(ValueError,match='provenance'):
        client.predict_remote(body)
