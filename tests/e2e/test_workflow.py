import os
import time
import uuid
import httpx
import pytest
from src.persistence.db import rows

pytestmark=pytest.mark.e2e


def test_inference_and_monitoring_are_separate_services():
    with httpx.Client(timeout=30) as client:
        inference=os.environ['INFERENCE_URI']
        monitor_uri=os.getenv('MONITOR_URI','http://monitoramento:8010')
        runtime=client.get(inference+'/health')
        assert runtime.status_code==200 and runtime.json()['service']=='inference'
        assert client.get(inference+'/ready').status_code==200
        monitor=client.get(monitor_uri+'/ready')
        assert monitor.status_code==200
        assert client.get(monitor_uri+'/v1/status').status_code==401


def test_all_models_trained_without_implicit_promotion():
    count=rows("SELECT count(DISTINCT model_id) AS n FROM planning.training_executions WHERE status='COMPLETED'")[0]['n']
    assert count>=30,'Execute train; e2e não inicia treinamento'
    unaudited=rows("""SELECT d.id FROM planning.model_deployments d WHERE NOT EXISTS
      (SELECT 1 FROM planning.audit_events a WHERE a.entity_id=d.id::text AND a.event_type='MODEL_PROMOTED')""")
    assert not unaudited


def test_batch_idempotency_and_traceable_suggestions():
    latest=rows("SELECT id,cycle_id FROM planning.dataset_snapshots WHERE sealed_at IS NOT NULL ORDER BY created_at DESC LIMIT 1")
    assert latest,'Execute seed'
    champions=rows("SELECT count(*) AS n FROM planning.model_deployments WHERE status='APPROVED' AND alias='champion'")[0]['n']
    assert champions==30,'Operador deve aprovar as 30 versões antes da aceitação; e2e não promove'
    payload=dict(cycle_id=str(latest[0]['cycle_id']),snapshot_id=str(latest[0]['id']),requested_by='e2e')
    headers={'Authorization':'Bearer '+os.environ['API_TOKEN'],'Idempotency-Key':'e2e-'+uuid.uuid4().hex}
    with httpx.Client(base_url=os.environ['API_URI'],headers=headers,timeout=120) as client:
        first=client.post('/v1/inference/batch',json=payload)
        assert first.status_code==202,first.text
        second=client.post('/v1/inference/batch',json=payload)
        assert second.status_code==202
        job_id=first.json()['job_id']
        assert job_id==second.json()['job_id']
        deadline=time.monotonic()+180
        while time.monotonic()<deadline:
            response=client.get('/v1/jobs/'+job_id)
            response.raise_for_status()
            state=response.json()
            if state['status'] not in ('PENDING','RUNNING'): break
            time.sleep(2)
        assert state['status']=='COMPLETED',state
        results=client.get(f'/v1/jobs/{job_id}/results').json()
        assert len(results)==30
        assert all(r['snapshot_id']==payload['snapshot_id'] and r['registered_version'] for r in results)
        offers=rows("""SELECT count(*) AS n FROM planning.offer_suggestions o JOIN planning.predictions p
            ON p.id=o.prediction_id WHERE p.job_id=:id""",{'id':job_id})[0]['n']
        assert offers==90
        single=client.post('/v1/inference/predict',json=dict(payload,model_key='C1-CR1-P1'))
        assert single.status_code==200,single.text
        assert single.json()['snapshot_id']==payload['snapshot_id']


def test_dashboard_authorization_and_log_query():
    url=os.getenv('DASHBOARD_URI','http://dashboard:8088')
    with httpx.Client(base_url=url,timeout=30) as client:
        assert client.get('/api/logs').status_code==401
        response=client.get('/api/logs',headers={'Authorization':'Bearer '+os.environ['DASHBOARD_TOKEN']},params={'service':'api','limit':10})
        assert response.status_code==200
        assert all(row['service']=='api' for row in response.json())
