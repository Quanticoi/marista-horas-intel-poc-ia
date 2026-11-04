"""Generate auditable, parameterized notebooks; no execution or deployment."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def notebook(name,title,sections):
    cells=[dict(cell_type="markdown",metadata={},source=f"# {title}\n\nPOC DEMO — contrato PROVISÓRIO / PENDENTE DE HOMOLOGAÇÃO. Execute em kernel novo. Credenciais somente por ambiente.\n")]
    for objective,code in sections:
        cells.extend([dict(cell_type="markdown",metadata={},source=objective),
                      dict(cell_type="code",metadata={},source=code,outputs=[],execution_count=None)])
    for i,c in enumerate(cells):
        c["id"]=f"catalog-{i}"
    body=dict(nbformat=4,nbformat_minor=5,cells=cells,metadata={"kernelspec":{"name":"pucpr","display_name":"PUCPR Python 3.12","language":"python"}})
    (ROOT/"notebooks"/f"{name}.ipynb").write_text(json.dumps(body,ensure_ascii=False,indent=1),encoding="utf-8")


setup='''import os, json
import pandas as pd
from IPython.display import display, Markdown
from src.workbench.journey_config import Settings
cfg=Settings.load()
'''
notebook("00_validacao_ambiente","Validação do ambiente",[("Configurar e verificar dependências reais. Esperado: tabela PASS; diagnóstico gera run identificada, sem treinar.",setup+'''from uuid import uuid4
from src.workbench.journey_steps import dependencies, require_dependencies
checks=dependencies(cfg,str(uuid4()))
display(pd.DataFrame(checks))
require_dependencies(checks,cfg)
''')])
notebook("02_teste_inferencia_planilha_turmas","Validação da proposta consumida pela aplicação",[
    ("1. Configuração e preflight somente leitura. Esperado: API, OpenAPI, autenticação e SDK disponíveis.",setup+'''from src.workbench.contract_review import preflight,candidates,fetch_payload,reconcile,report
from src.workbench.sdk import source_version
from src.common.lineage import utcnow
execution_id=os.getenv("PROPOSAL_ID", "")
page_size=50
max_rows=10000
profile="v44_partial"
invoke_demo_inference=False
display({"utc":utcnow(),"code_version":source_version(),"profile":profile})
display(pd.DataFrame(preflight(cfg)))
'''),
    ("2. Seleção controlada. Informe PROPOSAL_ID no ambiente ou execution_id nesta célula. Nenhuma proposta é selecionada automaticamente por data. Esperado: lista limitada por ciclo e UUID explícito.",'''display(pd.DataFrame(candidates(cfg)))
if not execution_id:
    raise ValueError("Defina execution_id com um UUID da tabela acima e execute novamente desde esta célula. Não será realizado treinamento.")
'''),
    ("3. Consumir o JSON HTTP integral com paginação, schema e hash. Esperado: páginas completas sem duplicação; este é o payload real da API.",'''pages,offers=fetch_payload(cfg,execution_id,page_size,max_rows)
for page in pages:
    display(page)
display(pd.json_normalize(offers))
'''),
    ("4. Regras funcionais. PASS técnico não homologa V4.4; dados ausentes devem resultar NOT_EVALUATED.",'''display(pd.DataFrame(pages[0]["validation"]))
assert not any(rule["status"]=="FAIL" for rule in pages[0]["validation"])
'''),
    ("5. Conferência independente de SQL, Registry e bytes RustFS/proxy; testes negativos sem alterar dados.",'''evidence=reconcile(cfg,execution_id,pages,offers)
display(evidence)
'''),
    ("6. Exportar evidências JSON/Markdown em artifacts/reports. A escrita é somente de relatórios.",'''report_path=report(execution_id,pages,evidence)
display(report_path)
display(Markdown("[MLflow](http://127.0.0.1:5000) · [API](http://127.0.0.1:8000/docs) · [RustFS](http://127.0.0.1:9001)"))
'''),
    ("7. Inferência adicional DEMO é opt-in. Não treina nem altera a proposta. Reutiliza referência explícita e entrada SQL da mesma geração.",'''if invoke_demo_inference:
    from src.workbench.contract_review import invoke_demo
    display(invoke_demo(cfg,execution_id))
else:
    display({"optional_inference":"NOT_EXECUTED", "reason":"opt-in desativado"})
''')])
notebook("03_exploracao_preparacao_dados","Exploração e preparação SQL",[
    ("Leitura versionada e filtros. Esperado: snapshot, tipos, nulos e amostra; nenhuma escrita.",setup+'''from src.data.journey import extract,prepare,QUERY
frame,snapshot=extract(cfg)
display(snapshot)
display(Markdown("```sql\\n"+QUERY.read_text()+"\\n```"))
display(frame.dtypes.astype(str))
display(frame.head())
display(frame.isna().sum())
'''),("Separação temporal sem ajuste de transformações. Esperado: três conjuntos ordenados no tempo.",'''train,evaluation,future=prepare(frame,snapshot)
display({"train":len(train),"evaluation":len(evaluation),"future":len(future)})
''')])
notebook("04_treinamento_individual","Treinamento individual explícito",[
    ("Selecione snapshot e model_key existentes. Treinamento desativado por padrão para evitar versões acidentais.",setup+'''from src.workbench.sdk import intake,train
snapshot_id=os.getenv("TRAIN_SNAPSHOT_ID", "")
model_key=os.getenv("TRAIN_MODEL_KEY", "C1-CR1-P1")
execute_training=False
display({"snapshot_id":snapshot_id,"model_key":model_key,"execute_training":execute_training})
'''),("Executar treino real somente após seleção e habilitação. Não promove versão.",'''if execute_training:
    if not snapshot_id:
        raise ValueError("Selecione TRAIN_SNAPSHOT_ID explicitamente")
    versions=train(snapshot_id,model_key=model_key)
    display(versions)
else:
    display({"status":"NOT_EXECUTED","reason":"Treinamento requer opt-in"})
''')])
notebook("05_treinamento_campanha","Campanhas e inventário de modelos",[
    ("Inventário real do catálogo e registros; não dispara 500 treinos. Campanhas persistentes/retry são evolução incremental ainda não habilitada.",setup+'''from src.workbench.contract_review import request
r=request(cfg,"/v1/models"); r.raise_for_status()
catalog=r.json()
display(pd.DataFrame(catalog))
display({"catalog_count":len(catalog),"campaign_scheduler":"NOT_IMPLEMENTED", "reason":"Submissão persistente com checkpoint/retry pendente; use treino individual explícito"})
''')])
notebook("06_avaliacao_comparativa","Comparação de execuções",[
    ("Consultar métricas de até 100 runs do experimento configurado. Esperado: métricas reais sem retreino.",setup+'''import mlflow
mlflow.set_tracking_uri(cfg.tracking)
client=mlflow.MlflowClient()
experiment=client.get_experiment_by_name(cfg.experiment)
if experiment is None:
    raise ValueError("Execute jornada01 para criar o experimento")
runs=client.search_runs([experiment.experiment_id],max_results=100)
display(pd.DataFrame([{ "run_id":r.info.run_id,"status":r.info.status,**r.data.metrics} for r in runs]))
''')])
notebook("07_registry_governanca","Registry e governança",[
    ("Consulta somente leitura. Tags/registro não equivalem a aprovação operacional; model_deployments é autoridade SQL.",setup+'''import mlflow
mlflow.set_tracking_uri(cfg.tracking)
client=mlflow.MlflowClient()
versions=client.search_model_versions("name='"+cfg.model_name+"'",max_results=100)
display(pd.DataFrame([{"model":v.name,"version":v.version,"run_id":v.run_id,"status":v.status,"tags":v.tags} for v in versions]))
from src.workbench.contract_review import request
r=request(cfg,"/v1/models"); r.raise_for_status()
display(pd.DataFrame(r.json()))
display({"promotion":"NOT_EXECUTED","reason":"Aprovação explícita de operador e justificativa exigidas pelo CLI promote"})
''')])
notebook("08_auditoria_lineage","Auditoria bidirecional de lineage",[
    ("Selecione proposta, run, model ou snapshot explicitamente. Esperado: vínculos reais paginados e legado identificado.",setup+'''from src.workbench.contract_review import request
kind="proposal"
external_id=os.getenv("PROPOSAL_ID", "")
if not external_id:
    raise ValueError("Informe external_id; exemplos de seleção no notebook02")
from urllib.parse import urlencode
response=request(cfg,"/v1/lineage?"+urlencode({"kind":kind,"external_id":external_id,"limit":100,"offset":0}))
response.raise_for_status()
display(response.json())
''')])
notebook("09_reset_total_ambiente_poc","Reset total — pré-visualização segura",[
    ("Run All nunca apaga dados. O controlador deve executar no host, pois factory-reset encerra este kernel. Primeiro gere o plano completo pelo terminal. Relatórios ficam fora dos volumes.",setup+'''from pathlib import Path
display(Markdown("No terminal do repositório: `python deployment/scripts/reset_poc.py preview --environment poc --project marista`"))
plan_id=os.getenv("RESET_PLAN_ID", "")
if plan_id:
    from uuid import UUID
    UUID(plan_id)
    path=Path("/reports/reset")/(plan_id+".plan.json")
    display(json.loads(path.read_text()))
else:
    display({"status":"PREVIEW_REQUIRED","reason":"Gere plano no host e informe RESET_PLAN_ID para examiná-lo aqui"})
display({"destructive_execution":"NOT_EXECUTED","confirmation":"Somente pelo controlador externo com plan_id e frase digitada"})
''')])
print("Generated notebook catalog 00–09; no execution")
