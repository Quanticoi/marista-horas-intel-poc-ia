import json
import tempfile
from pathlib import Path
import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature
from src.data.journey import FEATURES, TARGET, QUERY
from src.training.journey import SEED
from src.workbench.sdk import source_version


def start(cfg, execution_id, snapshot, frame):
    from src.common.lineage import Identity, sha256
    from src.persistence.journey import RULE
    identity = Identity(academic_cycle_id=snapshot["cycle_id"],snapshot_id=snapshot["id"],
        snapshot_sha256=snapshot["snapshot_sha256"],dataset_sha256=snapshot["dataset_sha256"],
        model_key=cfg.model_name,code_version=source_version(),config_hash=sha256({"alpha":1.0,"seed":SEED}),
        ruleset_version=RULE,ruleset_hash=sha256({"version":RULE,"capacity":40}),source_type=cfg.mode)
    exp = mlflow.get_experiment_by_name(cfg.experiment)
    eid = exp.experiment_id if exp else mlflow.create_experiment(cfg.experiment)
    exp = mlflow.get_experiment(eid)
    if not exp.artifact_location.startswith("mlflow-artifacts:"):
        raise ValueError("Use a new proxy experiment; legacy S3 experiment locations are immutable")
    run = mlflow.start_run(experiment_id=eid,
        run_name=f"{cfg.model_name}__{cfg.cycle}__{execution_id[:8]}", tags={
        **identity.tags(), "execution_id":execution_id, "correlation_id":execution_id, "mode":cfg.mode,
        "model_key":cfg.model_name,
        "purpose":"draft-planilha-turmas", "cycle":cfg.cycle, "scope":cfg.course or "all",
        "snapshot_id":snapshot["id"], "dataset_sha256":snapshot["dataset_sha256"],
        "query_sha256":snapshot["query_sha256"], "query_version":snapshot["query_version"],
        "code_version":source_version(), "selection_rule":"POC explicit version; no operational promotion",
        "requirements":"US027 partial DEMO; US016 technical audit; US017 original preservation"})
    mlflow.log_params({"algorithm":"Ridge", "alpha":1.0, "seed":SEED,
        "features":json.dumps(FEATURES), "target":TARGET, "rows":len(frame),
        "min_semester":int(frame.semester_index.min()), "max_semester":int(frame.semester_index.max()),
        "evaluation":"last semester; transformations fitted on earlier semesters only"})
    mlflow.log_artifact(str(QUERY), "reference")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "extraction.csv"
        frame.to_csv(path, index=False)
        mlflow.log_artifact(str(path), "reference")
    return {"run_id":run.info.run_id, "experiment_id":eid,
        "run_url":f"{cfg.ui}/#/experiments/{eid}/runs/{run.info.run_id}"}


def register(cfg, fitted, example, trace, execution_id):
    client = mlflow.MlflowClient()
    if trace.get("model_version"):
        # Repeating the notebook cell must not publish another version after
        # its in-memory fitted model has intentionally been discarded.
        version = client.get_model_version(cfg.model_name, trace["model_version"])
        if (trace.get("model_name") != cfg.model_name or version.run_id != trace["run_id"]
                or version.tags.get("execution_id") != execution_id
                or trace.get("model_uri") != f"models:/{cfg.model_name}/{version.version}"):
            raise ValueError("A versão registrada não pertence a esta execução")
        return trace
    if fitted is None:
        raise ValueError("Modelo treinado ausente: execute preparação, tracking e treinamento antes do registro")
    active = mlflow.active_run()
    if active is None or active.info.run_id != trace["run_id"]:
        raise ValueError("Registro requer a run de treinamento ativa desta execução")
    info = mlflow.sklearn.log_model(fitted, name="model",
        signature=infer_signature(example, fitted.predict(example)), input_example=example,
        pip_requirements=["mlflow==3.11.1", "scikit-learn==1.6.1", "numpy==2.2.2", "pandas==2.2.3", "cloudpickle==3.1.2"])
    version = mlflow.register_model(info.model_uri, cfg.model_name, await_registration_for=60)
    client.set_model_version_tag(cfg.model_name, version.version, "execution_id", execution_id)
    client.set_model_version_tag(cfg.model_name, version.version, "purpose", "draft-planilha-turmas")
    from src.common.lineage import sha256
    with tempfile.TemporaryDirectory() as folder:
        downloaded = Path(mlflow.artifacts.download_artifacts(artifact_uri=info.model_uri,dst_path=folder))
        artifact_sha256 = sha256((downloaded / "model.pkl").read_bytes())
    client.set_model_version_tag(cfg.model_name, version.version, "artifact_sha256", artifact_sha256)
    from src.common.lineage import CONTRACT
    for key, value in {**{k:v for k,v in client.get_run(trace["run_id"]).data.tags.items()
                         if k in ("model_key","snapshot_id","snapshot_sha256","code_version","source_type","config_hash","ruleset_hash")},
                       "run_id":trace["run_id"],"schema_version":CONTRACT,"validation_status":"DEMO_CANDIDATE"}.items():
        client.set_model_version_tag(cfg.model_name,version.version,key,value)
    return dict(trace, model_name=cfg.model_name, model_version=str(version.version),
        model_uri=f"models:/{cfg.model_name}/{version.version}", artifact_uri=version.source)
