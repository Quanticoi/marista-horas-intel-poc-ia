import os
import shutil
import sys
from pathlib import Path
from src.common.settings import required, database_url


def main():
    if sys.argv[1] == "mlflow":
        # URI is supplied through environment, never printed by our launcher.
        # MLflow accepts version IDs as strings. Psycopg 3 binds them as VARCHAR,
        # conflicting with the Registry INTEGER version column on PostgreSQL.
        # Keep psycopg 3 for application SQL; use psycopg2 for the MLflow server.
        os.environ["MLFLOW_BACKEND_STORE_URI"] = database_url("mlflow").set(
            drivername="postgresql+psycopg2").render_as_string(hide_password=False)
        # Supported migration command, executed before the listener is released.
        from src.persistence.mlflow_schema import upgrade
        upgrade()
        os.execvp("mlflow",["mlflow","server","--host","0.0.0.0","--port","5000",
                  "--serve-artifacts","--artifacts-destination",f"s3://{os.getenv('S3_BUCKET', 'pucpr-poc')}/mlflow",
                  "--allowed-hosts","mlflow:5000,127.0.0.1:*,localhost:*"])
    elif sys.argv[1] == "jupyter":
        workspace=Path("/workspace/notebooks")
        workspace.mkdir(parents=True,exist_ok=True)
        path = Path("/app/notebooks/01_jornada_completa_planilha_turmas.ipynb")
        if not (workspace/path.name).exists():
            shutil.copy2(path,workspace/path.name)
        os.environ["JUPYTER_TOKEN"]=required("JUPYTER_TOKEN")
        os.execvp("jupyter",["jupyter","lab","--ip=0.0.0.0","--port=8888","--no-browser",
            "--ServerApp.root_dir=/workspace",
            "--ServerApp.default_url=/lab/tree/notebooks/01_jornada_completa_planilha_turmas.ipynb"])
    else:
        raise ValueError("Unknown service")


if __name__ == "__main__":
    main()
