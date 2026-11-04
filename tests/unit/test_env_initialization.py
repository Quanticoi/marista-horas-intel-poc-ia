import importlib.util
from pathlib import Path
import pytest


def initializer():
    script=Path(__file__).resolve().parents[2]/'deployment/scripts/init_env.py'
    if not script.exists():
        pytest.skip('Host initializer requires deployment scripts mount')
    spec=importlib.util.spec_from_file_location('init_env',script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.initialize


def test_existing_credentials_and_repeat_are_preserved(tmp_path):
    initialize=initializer()
    target=tmp_path/'.env'
    original='POSTGRES_PASSWORD=existing-value\nMLFLOW_EXPERIMENT_NAME=my-experiment\n'
    target.write_text(original)
    initialize(tmp_path)
    first=target.read_bytes()
    assert first.startswith(original.encode())
    assert b'OPERATOR_TOKEN=' in first and b'INGESTION_TOKEN=' in first
    initialize(tmp_path)
    assert target.read_bytes()==first


def test_new_credentials_preserve_nonsecret_defaults(tmp_path):
    initialize=initializer()
    (tmp_path/'.env.example').write_text('POSTGRES_PASSWORD=\nOPERATOR_TOKEN=\nINGESTION_TOKEN=\nPROPOSAL_ID=\nMLFLOW_EXPERIMENT_NAME=demo\n')
    initialize(tmp_path)
    data=dict(line.split('=',1) for line in (tmp_path/'.env').read_text().splitlines())
    assert len(data['POSTGRES_PASSWORD'])==64
    assert data['PROPOSAL_ID']=='' and data['MLFLOW_EXPERIMENT_NAME']=='demo'
