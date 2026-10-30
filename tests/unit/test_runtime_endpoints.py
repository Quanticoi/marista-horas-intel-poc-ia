from contextlib import nullcontext
from unittest.mock import Mock
import httpx
import socket
from src.dashboard import main


def test_dashboard_uses_configured_dependencies(monkeypatch):
    values = {'DB_HOST':'db-test', 'RABBITMQ_HOST':'mq-test',
              'MLFLOW_S3_ENDPOINT_URL':'https://storage-test:9443',
              'API_URI':'http://api-test:8000', 'MLFLOW_TRACKING_URI':'http://tracking-test:5000',
              'INFERENCE_URI':'http://runtime-test:8001', 'MONITOR_URI':'http://monitor-test:8010'}
    for key,value in values.items():
        monkeypatch.setenv(key,value)
    tcp, urls = [], []
    def connect(address, timeout):
        tcp.append(address)
        return nullcontext()
    def get(url, timeout):
        urls.append(url)
        return Mock()
    monkeypatch.setattr(socket,'create_connection',connect)
    monkeypatch.setattr(httpx,'get',get)
    assert all(value.startswith('PASS') for value in main.services().values())
    assert tcp == [('db-test',5432),('mq-test',5672),('storage-test',9443)]
    assert urls == [values['API_URI']+'/ready',values['MLFLOW_TRACKING_URI']+'/health',
                    values['INFERENCE_URI']+'/ready',values['MONITOR_URI']+'/ready']


def test_compose_dashboard_does_not_contact_kubernetes(monkeypatch):
    monkeypatch.setenv('RUNTIME','compose')
    def forbidden():
        raise AssertionError('Compose must not query Kubernetes')
    monkeypatch.setattr(main,'kube',forbidden)
    assert main.resources()[0]['kind'] == 'Compose'
