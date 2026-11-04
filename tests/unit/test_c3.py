import copy
import io
from types import SimpleNamespace
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from src.training.estimator import SemesterForecaster
from src.training.models import forecast
from src.ingestion.contracts import Dataset
from src.workbench.sdk import test_dataset as sample_dataset
from src.mlops import artifacts


@pytest.mark.parametrize("algorithm", ["seasonal", "ridge", "forest"])
def test_fitted_binary_roundtrip_and_no_fit_at_prediction(tmp_path, monkeypatch, algorithm):
    import mlflow.sklearn
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor
    history = {4040+i:40+i*2+(i%2)*5 for i in range(12)}
    model = SemesterForecaster(algorithm).fit(history)
    frame = pd.DataFrame({"target_year":[2026],"target_semester":[1]})
    expected = forecast(history,4052,algorithm)
    path = tmp_path / "model"
    mlflow.sklearn.save_model(model,str(path),pip_requirements=[])
    restored = mlflow.sklearn.load_model(str(path))
    def forbidden(*args, **kwargs):
        pytest.fail("Prediction must not fit any estimator")
    monkeypatch.setattr(Ridge,"fit",forbidden)
    monkeypatch.setattr(RandomForestRegressor,"fit",forbidden)
    np.testing.assert_allclose(restored.predict(frame),[expected])


def test_bundle_reads_every_file_and_rejects_corruption_before_deserialization(tmp_path, monkeypatch):
    (tmp_path/"MLmodel").write_bytes(b"descriptor")
    (tmp_path/"model.pkl").write_bytes(b"trusted-binary")
    checksum = artifacts.manifest(tmp_path,dict(model_key="test"))
    objects={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    monkeypatch.setattr(artifacts,"s3",lambda:SimpleNamespace(get_object=lambda **kw:
        {"Body":io.BytesIO(objects[kw["Key"].split('/')[-1]])}))
    monkeypatch.setattr(artifacts.mlflow.sklearn,"load_model",lambda path: "loaded")
    assert artifacts.load_bundle("s3://pucpr-poc/mlflow/run/model",checksum)[0]=="loaded"
    objects['model.pkl']=b'tampered'
    with pytest.raises(ValueError,match="checksum"):
        artifacts.load_bundle("s3://pucpr-poc/mlflow/run/model",checksum)
    with pytest.raises(ValueError,match="Bundle checksum"):
        artifacts.load_bundle("s3://pucpr-poc/mlflow/run/model",'0'*64)


def test_dataset_rejects_invalid_inputs_and_temporal_leakage():
    payload=sample_dataset()
    assert len(Dataset.model_validate(payload).records)==350
    for modify in [lambda p:p['records'].append(p['records'][0]),
                   lambda p:p['records'][0].update(regular_students=-1),
                   lambda p:p['records'][0].update(regular_students=1.5),
                   lambda p:p['records'][0].update(reference_semester=True),
                   lambda p:p.update(as_of_date='2025-06-30'),
                   lambda p:p.update(target_year=2025),
                   lambda p:p.update(records=p['records'][:1]),
                   lambda p:p.update(target_semester=True),
                   lambda p:p['records'][0].update(campus_id='wrong'),
                   lambda p:p['records'][0].update(secret_extra='no')]:
        bad=copy.deepcopy(payload)
        modify(bad)
        with pytest.raises((ValidationError,ValueError)):
            Dataset.model_validate(bad)


def test_ingestion_rejects_unauthorized_and_oversize(monkeypatch):
    from src.ingestion.main import app
    monkeypatch.setenv('INGESTION_TOKEN','intake-test')
    client=TestClient(app)
    assert client.get('/v1/datasets').status_code==401
    assert client.post('/v1/datasets',json=sample_dataset()).status_code==401
    assert client.post('/v1/datasets',content=b'x'*(4*1024*1024+1)).status_code==413


def test_sdk_refuses_local_mlflow_fallback(monkeypatch):
    from src.workbench.sdk import connect
    monkeypatch.setenv('MLFLOW_TRACKING_URI','sqlite:///mlflow.db')
    with pytest.raises(ValueError,match='remote'):
        connect()


def test_dedicated_model_rejects_other_model_without_execution(monkeypatch):
    import uuid
    from src.inference import model_api
    deployment=uuid.uuid4()
    monkeypatch.setenv('MODEL_KEY','C1-CR1-P1')
    monkeypatch.setenv('REGISTERED_VERSION','2')
    monkeypatch.setenv('MODEL_DEPLOYMENT_ID',str(deployment))
    monkeypatch.setenv('INFERENCE_TOKEN','test-token')
    monkeypatch.setattr(model_api,'infer',lambda body:pytest.fail('Wrong model must not execute'))
    client=TestClient(model_api.app)
    response=client.post('/internal/predict',headers={'Authorization':'Bearer test-token'},json={
        'model_key':'C1-CR1-P2','deployment_id':str(deployment),'snapshot_id':str(uuid.uuid4()),
        'target_year':2026,'target_semester':1})
    assert response.status_code==409


def test_router_uses_dedicated_server_and_checks_response(monkeypatch):
    import uuid
    from src.inference import routing
    from src.inference.contracts import InferenceRequest
    request=InferenceRequest(deployment_id=uuid.uuid4(),snapshot_id=uuid.uuid4(),
        model_key='C1-CR1-P1',target_year=2026,target_semester=1)
    result=dict(deployment_id=str(request.deployment_id),snapshot_id=str(request.snapshot_id),
        model_key=request.model_key,registered_version='1',forecast_raw=12,is_fallback=False)
    monkeypatch.setenv('INFERENCE_TOKEN','internal')
    calls=[]
    def post(url,**kwargs):
        calls.append(url)
        return SimpleNamespace(raise_for_status=lambda:None,json=lambda:result)
    monkeypatch.setattr(routing.httpx,'post',post)
    assert routing.route(request).forecast_raw==12
    assert calls==[f'http://{routing.service_name(request.model_key)}:8001/internal/predict']
    result['model_key']='another-model'
    with pytest.raises(ValueError,match='provenance'):
        routing.route(request)
