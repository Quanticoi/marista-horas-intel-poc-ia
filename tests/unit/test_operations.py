import pytest
from pydantic import ValidationError
from src.operations.contracts import Campaign,Generation
from src.workbench.notebook_config import Parameters

@pytest.fixture
def campaign_request():
    return dict(snapshot_id="fb931e1e-43d0-5ff8-938c-0d2ba4a68794",cycle_code="2026-1",
        model_keys=["hi.demo.one"],requested_by="test",confirm_training=True)

@pytest.mark.parametrize("change",[{"model_keys":["hi.demo.one","hi.demo.one"]},{"model_keys":["arbitrary"]},{"max_parallel_jobs":500},{"alpha":-1},{"confirm_training":False},{"algorithm":"unknown"}])
def test_campaign_rejects_unsafe_parameters(campaign_request,change):
    with pytest.raises(ValidationError): Campaign(**dict(campaign_request,**change))

def test_notebook_requires_stable_explicit_confirmation():
    with pytest.raises(ValueError): Parameters(execute_write=True).authorize()
    Parameters(execute_write=True,confirmation="EXECUTE_DEMO",request_key="same-attempt").authorize()

def test_generation_rejects_duplicate_model_mapping():
    with pytest.raises(ValidationError):
        Generation(cycle_code="2026-1",snapshot_id="fb931e1e-43d0-5ff8-938c-0d2ba4a68794",
            model_selectors=[dict(model_name="planilha-turmas-demo",model_version="1")]*2,requested_by="test",confirm_demo=True)
