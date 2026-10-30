import uuid
import pytest
from fastapi.testclient import TestClient
from src.api.main import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('API_TOKEN','test-only-token')
    return TestClient(app)


def test_auth_and_invalid_correlation(client):
    assert client.get('/health').status_code==200
    response=client.get('/v1/models')
    assert response.status_code==401
    assert set(response.json())=={'code','message','correlation_id'}
    assert client.get('/health',headers={'X-Correlation-ID':'invalid space'}).status_code==422


def test_batch_requires_idempotency_key(client):
    response=client.post('/v1/inference/batch',headers={'Authorization':'Bearer test-only-token'},
        json=dict(cycle_id=str(uuid.uuid4()),snapshot_id=str(uuid.uuid4()),requested_by='test'))
    assert response.status_code==422


def test_pagination_bounds(client):
    response=client.get('/v1/predictions?limit=1001',headers={'Authorization':'Bearer test-only-token'})
    assert response.status_code==422


def test_payload_is_bounded(client):
    response=client.post('/v1/inference/batch',content=b'x'*65537)
    assert response.status_code==413
