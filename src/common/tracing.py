"""Bounded per-cell traces, with W3C propagation and metadata-only capture."""
import os
from contextlib import contextmanager
from functools import lru_cache

import mlflow
from mlflow.entities import SpanStatus, SpanStatusCode
from mlflow.entities.trace_location import MlflowExperimentLocation
from mlflow.tracing import (get_tracing_context_headers_for_http_request,
                            set_tracing_context_from_http_request_headers)

_experiment_id = None


def configure_tracing(cfg):
    global _experiment_id
    experiment = mlflow.set_experiment(cfg.experiment)
    _experiment_id = experiment.experiment_id
    return _experiment_id


@contextmanager
def safe_span(name, attributes, experiment_id=None):
    """Do not export input data, headers, SQL parameters or exception messages."""
    caught = None
    destination = MlflowExperimentLocation(experiment_id) if experiment_id else None
    with mlflow.start_span(name=name, attributes=attributes, trace_destination=destination) as span:
        if span.trace_id == "MLFLOW_NO_OP_SPAN_TRACE_ID":
            raise RuntimeError("Tracing indisponível: nenhum span foi criado")
        try:
            yield span
        except Exception as error:
            span.set_attribute("error.type", type(error).__name__)
            span.set_status(SpanStatus(SpanStatusCode.ERROR))
            caught = error
    if caught is not None:
        raise caught


@contextmanager
def stage_span(name, execution_id, attempt):
    if _experiment_id is None:
        yield None
        return
    with safe_span(name, {"service": "jupyter", "execution_id": execution_id,
                        "stage": name, "attempt": attempt}, _experiment_id) as span:
        mlflow.update_current_trace(tags={"execution_id": execution_id, "stage": name},
                                    client_request_id=execution_id)
        yield span


def trace_headers():
    return get_tracing_context_headers_for_http_request()


@contextmanager
def operation_span(name, **attributes):
    if mlflow.get_current_active_span() is None:
        yield None
        return
    with safe_span(name, attributes) as span:
        yield span


@lru_cache(maxsize=1)
def service_experiment():
    name=os.getenv('MLFLOW_OPERATIONS_EXPERIMENT_NAME',os.environ['MLFLOW_EXPERIMENT_NAME'])
    experiment = mlflow.MlflowClient().get_experiment_by_name(name)
    if experiment is None:
        raise RuntimeError("Configure o experimento da jornada antes de chamar a API")
    return experiment.experiment_id


def install_http_tracing(app, service, prefix):
    @app.middleware("http")
    async def traced_request(request, call_next):
        # Only calls carrying a notebook trace are instrumented. Health checks
        # and ordinary browsing do not create experiments or traces.
        if not request.url.path.startswith(prefix) or "traceparent" not in request.headers:
            return await call_next(request)
        context_headers = {k: request.headers[k] for k in ("traceparent", "tracestate") if k in request.headers}
        # Configure the destination before adopting the remote parent. Passing
        # a destination to a child span is not supported by MLflow 3.11.
        mlflow.tracing.set_destination(MlflowExperimentLocation(service_experiment()), context_local=True)
        with set_tracing_context_from_http_request_headers(context_headers):
            with safe_span(f"{service}.http", {"service": service, "http.method": request.method}) as span:
                response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)
                if response.status_code >= 400:
                    span.set_status(SpanStatus(SpanStatusCode.ERROR))
                response.headers["X-MLflow-Trace-ID"] = span.trace_id
                return response


def trace_evidence(cfg, statuses, trace, execution_id):
    mlflow.flush_trace_async_logging()
    client = mlflow.MlflowClient()
    evidence = []
    for status in statuses:
        trace_id = status.get("trace_id")
        if not trace_id:
            continue
        for key, value in {"execution_id": execution_id, "run_id": trace["run_id"],
                           "model_name": trace["model_name"], "model_version": trace["model_version"]}.items():
            client.set_trace_tag(trace_id, key, value)
        recorded = mlflow.get_trace(trace_id)
        if recorded is None:
            raise RuntimeError(f"Trace não persistido: {trace_id}")
        evidence.append({"stage": status["stage"], "attempt": status["attempt"], "trace_id": trace_id,
                         "spans": [s.name for s in recorded.data.spans],
                         "url": f"{cfg.ui}/#/experiments/{trace['experiment_id']}/traces?selectedEvaluationId={trace_id}&compareRunsMode=TRACES"})
    return evidence
