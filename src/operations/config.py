import os
from src.common.settings import database_url,required
from src.workbench.journey_config import Settings

def settings(cycle):
    return Settings(source=database_url("app").render_as_string(hide_password=False),
        application=database_url("app").render_as_string(hide_password=False),
        tracking=required("MLFLOW_TRACKING_URI"),ui=os.getenv("MLFLOW_UI_BASE_URL","http://127.0.0.1:5000"),
        experiment=os.getenv("MLFLOW_EXPERIMENT_NAME","planilha-turmas-proxy-v1"),
        model_name="planilha-turmas-demo",api=required("API_URI"),inference=required("INFERENCE_URI"),cycle=cycle)
