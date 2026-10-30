"""Notebook/CLI training: remote metadata services and persisted fitted binaries."""
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
import cloudpickle
import src.training.estimator as estimator_module
import src.training.models as models_module
from mlflow import MlflowClient
from mlflow.models import infer_signature
from mlflow.exceptions import MlflowException
from src.common.settings import config
from src.training.models import select
from src.training.estimator import SemesterForecaster
from src.mlops.artifacts import manifest, digest, load_bundle
from src.workbench.sdk import connect, intake, source_version


def train(snapshot_id, model_key=None):
    connect()
    snapshot = intake("GET", f"/v1/datasets/{snapshot_id}")
    frame = pd.DataFrame(snapshot["records"])
    if model_key is not None:
        frame = frame[frame.model_key == model_key]
    if frame.empty:
        raise ValueError("No matching series in snapshot")
    code = source_version()
    cfg_hash = digest(json.dumps(config("training"), sort_keys=True).encode())
    mlflow.set_experiment("pucpr-synthetic")
    result = []
    for key, group in frame.groupby("model_key"):
        history = {int(r.reference_year)*2+int(r.reference_semester)-1:
                   int(r.regular_students+r.dependency_students+r.elective_students) for r in group.itertuples()}
        algorithm, scores, fallback = select(history)
        run_id = None
        started = False
        try:
            with mlflow.start_run(tags={"snapshot_id":str(snapshot_id), "model_key":key,
                    "code_version":code, "config_hash":cfg_hash, "dataset_sha256":snapshot["sha256"],
                    "source":snapshot["source_reference"], "bundle_schema":"2.0"}) as run:
                run_id = run.info.run_id
                intake("POST", "/v1/training", dict(snapshot_id=str(snapshot_id), model_key=key,
                    algorithm=algorithm, code_version=code, config_hash=cfg_hash, run_id=run_id))
                started = True
                mlflow.log_params({"algorithm":algorithm, "fallback":fallback, "history_length":len(history)})
                for name, score in scores.items():
                    if score:
                        mlflow.log_metrics({f"{name}_{k}":v for k,v in score.items()})
                mlflow.log_metrics(scores[algorithm])
                fitted = SemesterForecaster(algorithm).fit(history)
                target = max(history)+1
                sample = pd.DataFrame({"target_year":[target//2], "target_semester":[target%2+1]})
                expected = fitted.predict(sample)
                provenance = dict(model_key=key, snapshot_id=str(snapshot_id), run_id=run_id,
                    code_version=code, dataset_sha256=snapshot["sha256"], config_hash=cfg_hash,
                    algorithm=algorithm, fallback=fallback,
                    smoke_input=sample.to_dict("records"), smoke_prediction=expected.tolist())
                uri = run.info.artifact_uri.rstrip("/") + "/model"
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "model"
                    # Embed our preprocessing/prediction code, not just a reference to the current image.
                    for module in (estimator_module, models_module):
                        cloudpickle.register_pickle_by_value(module)
                    try:
                        mlflow.sklearn.save_model(fitted, str(path), signature=infer_signature(sample, expected),
                            input_example=sample,
                            pip_requirements=["mlflow==3.11.1", "scikit-learn==1.6.1", "numpy==2.2.2", "pandas==2.2.3", "cloudpickle==3.1.2"])
                    finally:
                        for module in (estimator_module, models_module):
                            cloudpickle.unregister_pickle_by_value(module)
                    checksum = manifest(path, provenance)
                    mlflow.log_artifacts(str(path), "model")
                # Verify persistence and round-trip predictions before creating a Registry version.
                restored, _ = load_bundle(uri, checksum)
                np.testing.assert_allclose(restored.predict(sample), expected, rtol=1e-12, atol=1e-12)
                client = MlflowClient()
                try:
                    client.create_registered_model(key)
                except MlflowException as error:
                    if error.error_code != "RESOURCE_ALREADY_EXISTS":
                        raise
                version = client.create_model_version(key, uri, run_id,
                    tags={"snapshot_id":str(snapshot_id), "schema_version":"2.0", "bundle_sha256":checksum,
                          "code_version":code, "dataset_sha256":snapshot["sha256"]})
                result.append(dict(model_key=key, version=str(version.version), run_id=run_id,
                                   artifact_uri=uri, bundle_sha256=checksum, approved=False))
        finally:
            if started:
                intake("POST", f"/v1/training/{run_id}/sync")
    return result
