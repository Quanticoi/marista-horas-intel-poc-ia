from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.mlops import journey
from src.workbench.journey_steps import step


def test_repeat_registration_reuses_owned_version_without_model(monkeypatch):
    client = Mock()
    client.get_model_version.return_value = SimpleNamespace(
        version="6", run_id="run", tags={"execution_id": "execution"})
    monkeypatch.setattr(journey.mlflow, "MlflowClient", lambda: client)
    publish = Mock(side_effect=AssertionError("must not publish again"))
    monkeypatch.setattr(journey.mlflow.sklearn, "log_model", publish)
    trace = dict(model_name="demo", model_version="6", run_id="run", model_uri="models:/demo/6")
    assert journey.register(SimpleNamespace(model_name="demo"), None, None, trace, "execution") == trace
    publish.assert_not_called()
    with pytest.raises(ValueError, match="não pertence"):
        journey.register(SimpleNamespace(model_name="demo"), None, None, trace, "other-execution")


def test_missing_fitted_model_is_reported_before_logging(monkeypatch):
    monkeypatch.setattr(journey.mlflow, "MlflowClient", Mock())
    with pytest.raises(ValueError, match="Modelo treinado ausente"):
        journey.register(SimpleNamespace(model_name="demo"), None, None, {"run_id": "run"}, "execution")


def test_missing_name_is_visible_and_secrets_are_not_echoed(monkeypatch):
    monkeypatch.setattr(journey.mlflow, "active_run", lambda: None)
    statuses = []
    with pytest.raises(RuntimeError, match="Nome não definido: model") as error:
        with step("register", "execution", statuses):
            raise NameError("password=do-not-print", name="model")
    assert "do-not-print" not in str(error.value)
    assert statuses[0]["status"] == "FAILED"
