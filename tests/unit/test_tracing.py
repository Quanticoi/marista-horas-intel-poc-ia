from contextlib import contextmanager
from unittest.mock import Mock

import pytest
from src.common import tracing


def test_trace_failure_does_not_capture_exception_payload(monkeypatch):
    span = Mock()
    @contextmanager
    def start_span(**kwargs):
        try:
            yield span
        except Exception:
            pytest.fail("Raw exception reached MLflow automatic recording")
    monkeypatch.setattr(tracing.mlflow, "start_span", start_span)
    with pytest.raises(ValueError):
        with tracing.safe_span("failure", {}):
            raise ValueError("password=never-record")
    span.set_attribute.assert_called_once_with("error.type", "ValueError")
    span.set_status.assert_called_once()
    span.set_inputs.assert_not_called()
    span.set_outputs.assert_not_called()
