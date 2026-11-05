"""Small notebook presentation helpers; scientific/operational boundaries remain explicit."""
import os
import pandas as pd
from src.persistence.db import rows
from src.workbench.application_client import context,save_context


def snapshot_id():
    selected=os.getenv('V4_SNAPSHOT_ID') or context().get('snapshot_id')
    if selected:
        return selected
    found=rows("SELECT snapshot_id FROM planning.academic_simulation_snapshots WHERE seed=42 AND scenario_id='baseline' AND cycle_code='2024-2'")
    if len(found)!=1:
        raise ValueError('Selecione explicitamente snapshot_id do notebook03; cenário baseline ausente ou ambíguo.')
    selected=str(found[0]['snapshot_id']);save_context(snapshot_id=selected)
    return selected


def references():
    return [r['payload'] for r in rows('SELECT payload FROM planning.academic_reference_rows ORDER BY source_file_sha256,source_row_number')]


def metric_controls(profile='forecast_extended'):
    import ipywidgets as widgets
    from IPython.display import display
    from src.workbench.metrics_v4 import catalog,profile as read_profile
    selected=read_profile(profile)['selected']
    boxes={m['metric_id']:widgets.Checkbox(value=m['metric_id'] in selected,description=m['metric_id']) for m in catalog()['metrics']}
    display(widgets.VBox(list(boxes.values())))
    return boxes


def model_table(models):
    ui=os.environ['MLFLOW_UI_BASE_URL'].rstrip('/')
    return pd.DataFrame([dict(Curso=m['course_code'],Modelo=m['model_name'],Versão=m['model_version'],Algoritmo=m['algorithm'],
        Qualidade=m['validation_status'],MAE_regular=m['metrics'].get('regular.mae'),RMSE_regular=m['metrics'].get('regular.rmse'),
        Run=ui+f"/#/experiments/{m['experiment_id']}/runs/{m['run_id']}",Registry=ui+f"/#/models/{m['model_name']}/versions/{m['model_version']}",
        Manifesto=m.get('manifest',{}).get('uri'),SHA256=m['artifact_sha256']) for m in models])


def campaign_result():
    cid=context().get('campaign_id')
    if not cid:
        raise ValueError('Execute 04 ou 05 para selecionar uma campanha explícita.')
    found=rows('SELECT result FROM planning.workbench_campaigns WHERE campaign_id=:id',{'id':cid})
    if not found:
        raise ValueError('Campanha selecionada não encontrada')
    return found[0]['result']
