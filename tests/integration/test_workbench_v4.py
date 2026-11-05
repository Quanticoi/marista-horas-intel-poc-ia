import json
from pathlib import Path
import mlflow
import mlflow.sklearn
import pytest
from src.workbench.academic_campaign import execute,require_workbench
from src.workbench.academic_data import load,prepare,FEATURES
from src.workbench.verification import verify_model_storage


@pytest.fixture(scope='module')
def evidence():
    path=Path('/reports/v4/training-evidence.json')
    if not path.exists():
        pytest.skip('Run the V4 Workbench pilot before checking real Registry evidence')
    return json.loads(path.read_text())


def test_three_real_models_and_artifact_identity(evidence):
    assert evidence['status']=='COMPLETED'
    models=evidence['models']
    assert len(models)==3
    assert {r['course_code'] for r in models}=={'2248','2348','2287'}
    assert {r['algorithm'] for r in models}=={'ridge','dummy'}
    assert len({r['artifact_sha256'] for r in models})==3
    assert all(r['executor_pid']>0 and r['evaluations'] for r in models)
    client=mlflow.MlflowClient()
    for model in models:
        run=client.get_run(model['run_id'])
        assert run.info.status=='FINISHED'
        assert run.data.tags['executor']=='JUPYTER_WORKBENCH'
        assert run.data.metrics['artifact_bytes']>0
        assert run.data.metrics['process_peak_rss_bytes']>0
        storage=verify_model_storage(model)
        assert next(f['sha256'] for f in storage if f['key'].endswith('/model.pkl'))==model['artifact_sha256']


@pytest.mark.skipif(not Path('/opt/conda').is_dir(),reason='Execute the Workbench integration suite in the Jupyter container')
def test_repeat_campaign_has_no_new_run_or_version(evidence):
    repeated=execute(evidence['snapshot_id'],'v4-workbench-pilot-001')
    assert repeated==evidence


def test_persisted_models_reload_for_future_inputs(evidence):
    frame,_=load(evidence['snapshot_id'])
    for model in evidence['models']:
        restored=mlflow.sklearn.load_model(model['model_uri'])
        _,_,future=prepare(frame,model['course_code'])
        prediction=restored.predict(future[FEATURES])
        assert prediction.shape==(len(future),3)


def test_non_workbench_execution_is_rejected(monkeypatch):
    monkeypatch.delenv('WORKBENCH_EXECUTOR',raising=False)
    with pytest.raises(RuntimeError,match='Workbench'):
        require_workbench()
