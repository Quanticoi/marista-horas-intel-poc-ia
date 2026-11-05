import importlib.util
from pathlib import Path
from datetime import datetime,timezone
import pytest

script=Path(__file__).resolve().parents[2]/"deployment/scripts/reset_poc.py"


@pytest.fixture
def reset():
    if not script.exists():
        pytest.skip("Host controller is validated with deployment mount")
    spec=importlib.util.spec_from_file_location("reset_poc",script)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("environment",["dev","qa","uat","prd"])
def test_wrong_environment(reset,environment):
    with pytest.raises(ValueError):
        reset.validate_scope(environment,"marista")


def test_scope_and_confirmation(reset):
    with pytest.raises(ValueError):
        reset.validate_scope("poc","another-project")
    with pytest.raises(ValueError):
        reset.validate_plan({},"yes",True,"poc","marista")
    with pytest.raises(ValueError):
        reset.validate_plan({},reset.PHRASE,False,"poc","marista")
    for environment in (None,"dev","qa","uat","prd"):
        with pytest.raises(ValueError):
            reset.validate_labels({"io.marista.environment":environment,"io.marista.solution":"horarios-inteligentes"})


def test_tampered_and_stale(reset,monkeypatch):
    plan=dict(environment="poc",scope={"project":"marista"},created_at_utc=datetime.now(timezone.utc).isoformat(),inventory={},preserved={})
    plan["plan_hash"]=reset.digest(plan)
    monkeypatch.setattr(reset,"validate_scope",lambda *_:{"project":"different"})
    with pytest.raises(ValueError,match="Stale"):
        reset.validate_plan(plan,reset.PHRASE,True,"poc","marista")
    plan["inventory"]={"tampered":True}
    with pytest.raises(ValueError,match="Modified"):
        reset.validate_plan(plan,reset.PHRASE,True,"poc","marista")


def test_selective_reset_has_own_confirmation(reset):
    with pytest.raises(ValueError,match='confirmation'):
        reset.validate_plan({'mode':'reset-experiments'},reset.PHRASE,True,'poc','marista')
    with pytest.raises(ValueError,match='do not reseed'):
        reset.execute_plan({'mode':'reset-experiments'},'poc','marista',reset.EXPERIMENT_PHRASE,True,'demo-ready')
