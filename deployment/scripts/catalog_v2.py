"""V2 notebook cells describe each operation; reusable logic lives in src/workbench."""
def build(notebook,setup):
    setup+='''from src.workbench.notebook_config import Parameters
from src.workbench.operations_sdk import call, report, await_job
params=Parameters.load()
display(params.model_dump(mode="json"))
from src.workbench.manual_validation import display_locations, audit, export_session
display({"state":"READY", "write_enabled":params.execute_write, "tracking":"remote Docker service", "browser_ui":cfg.ui})
evidence={}
'''
    end='''report_status="PARTIAL" if any(isinstance(value,str) and value.startswith("NOT_EXECUTED") for value in evidence.values()) else "PASS"
if evidence.get("campaign",{}).get("status") in ("FAILED","PARTIAL","CANCELLED","PAUSED"):
    report_status="PARTIAL"
display(report(NOTEBOOK_ID,evidence,status=report_status,generation="v3",limitations=["Dados DEMO e contrato provisório; regras não avaliadas não são homologação", "Execução sem erro do notebook não implica execução de operações opt-in desativadas"]))
'''
    def emit(name,title,sections):
        intro=("Configuração tipada. Pré-requisitos: Docker saudável, seed DEMO, token por ambiente. Entradas: parâmetros abaixo; saídas: tabelas, IDs e relatório JSON/Markdown. Escritas exigem confirmação EXECUTE_DEMO e chave estável; repetir chave igual recupera o mesmo job. Espere READY; erros de dependência exigem verificar docker compose logs.",
               setup+f'NOTEBOOK_ID="{name}"\n')
        notebook(name,title,[intro,*sections,("Guardar evidência desta execução e links. Esperado: caminho do relatório, sem credenciais.",end)])
    emit("00_validacao_ambiente","Dependências e versões",[
        ("1. SQL e tracking real com pequeno artefato diagnóstico. Esperado: tabela PASS, antes de qualquer treino.",'''from uuid import uuid4
from src.workbench.journey_steps import dependencies, require_dependencies
checks=dependencies(cfg,str(uuid4()))
display(pd.DataFrame(checks)); require_dependencies(checks,cfg)
evidence["dependencies"]=checks
'''),("2. Serviços, storage e versões. API /ready valida RabbitMQ; falha resulta NOT_READY.",'''from src.workbench.exploration import service_checks
import mlflow,sklearn,numpy
services=service_checks();display(pd.DataFrame(services))
assert all(s["status"]=="PASS" for s in services), "NOT_READY: veja diagnóstico por serviço"
evidence.update(services=services,versions={"mlflow":mlflow.__version__,"sklearn":sklearn.__version__,"numpy":numpy.__version__})
''')])
    emit("02_teste_inferencia_planilha_turmas","Gerar pela API ou conferir uma proposta",[
        ("1. Preflight e seleção. READ_EXISTING não escreve; GENERATE_AND_VALIDATE envia POST ao worker. Escolha explicitamente snapshot e modelo/versão; confirme a escrita e defina request_key.",'''from src.workbench.contract_review import preflight,candidates,fetch_payload,reconcile
display(pd.DataFrame(preflight(cfg)));display(pd.DataFrame(candidates(cfg)))
proposal_id=str(params.proposal_id) if params.proposal_id else ""
'''),("2. Submeter geração somente no modo opt-in. Nenhuma persistência é feita pelo notebook. Esperado: job, correlation_id e status_url.",'''if params.mode=="GENERATE_AND_VALIDATE":
    params.authorize()
    if not params.snapshot_id or not params.model_version:
        raise ValueError("Selecione snapshot_id e model_version explicitamente")
    from src.workbench.operations_sdk import generate
    payload=dict(cycle_code=cfg.cycle,snapshot_id=str(params.snapshot_id),
        model_selectors=[dict(model_name=params.model_name,model_version=params.model_version)],
        capacity=params.capacity,requested_by=params.requester,confirm_demo=True)
    display(payload)
    submitted=generate(cfg,payload,params.request_key)
    display(submitted)
    finished=await_job(cfg,submitted["status_url"])
    if finished["status"]!="COMPLETED":
        raise RuntimeError("Geração não completou; consulte o job persistido: "+str(finished))
    proposal_id=finished["proposal_id"]
    evidence.update(request=payload,job=finished)
if not proposal_id:
    raise ValueError("Selecione proposal_id da tabela ou configure modo GENERATE_AND_VALIDATE")
'''),("3. Obter payload integral paginado e validar schema/hash. Este é o JSON consumido pela aplicação.",'''pages,offers=fetch_payload(cfg,proposal_id,page_size=50)
for page in pages: display(page)
display(pd.json_normalize(offers))
display(pd.DataFrame(pages[0]["validation"]))
assert not any(r["status"]=="FAIL" for r in pages[0]["validation"])
evidence.update(proposal_id=proposal_id,http_pages=pages)
'''),("4. Reconciliação somente leitura: linhas SQL, versões Registry, snapshot e bytes RustFS. Esperado: mesmos IDs, quantidades e hashes.",'''evidence["reconciliation"]=reconcile(cfg,proposal_id,pages,offers)
display(evidence["reconciliation"])
display(Markdown(f"[API](http://localhost:8000/v1/proposals/{proposal_id}/application-view) · [MLflow]({cfg.ui}) · [RustFS](http://localhost:9001)"))
''')])
    emit("03_exploracao_preparacao_dados","Exploração SQL e separação temporal",[
        ("1. Mostrar SQL versionado, recorte, fonte e qualidade. Esperado: dados sintéticos lidos por conexão SQL fechada pelo módulo.",'''from src.data.journey import extract,prepare,QUERY,KEYS
frame,snapshot=extract(cfg,snapshot_id=str(params.snapshot_id) if params.snapshot_id else None)
display(Markdown("```sql\\n"+QUERY.read_text()+"\\n```"));display(snapshot)
display(frame.dtypes.astype(str));display(frame.head(12));display(frame.describe(include="all"))
display(frame.isna().sum());assert not frame.duplicated(KEYS+["semester_index"]).any()
evidence.update(snapshot=snapshot,rows=len(frame),nulls=frame.isna().sum().to_dict())
'''),("2. Evolução e split temporal. Transformações serão ajustadas somente no treino.",'''from IPython.display import SVG
from src.workbench.exploration import series_svg
display(SVG(series_svg(frame)))
train,evaluation,future=prepare(frame,snapshot)
split={"train":len(train),"evaluation":len(evaluation),"future":len(future),"train_max":int(train.semester_index.max()),"evaluation_min":int(evaluation.semester_index.min()),"future_min":int(future.semester_index.min())}
display(split);evidence["split"]=split
''')])
    training='''from src.workbench.operations_sdk import campaign
if params.execute_write:
    params.authorize()
    if not params.snapshot_id:
        raise ValueError("Selecione snapshot_id da tabela SQL")
    payload=dict(snapshot_id=str(params.snapshot_id),cycle_code=cfg.cycle,model_keys=model_keys,
        algorithm=params.algorithm,alpha=params.alpha,max_parallel_jobs=params.parallel_jobs,
        requested_by=params.requester,confirm_training=True,campaign_display_name=params.campaign_display_name)
    display({"preflight":payload,"budget":"máximo 2 processos, 2 GiB no container worker; identidades experimentais sintéticas"})
    submitted=campaign(cfg,payload,params.request_key)
    campaign_id=submitted["campaign_id"]
else:
    campaign_id=str(params.campaign_id) if params.campaign_id else ""
if campaign_id:
    state=await_job(cfg,f"/v1/training/campaigns/{campaign_id}",timeout=7200)
    items=call(cfg,"GET",f"/v1/training/campaigns/{campaign_id}/items?limit=500")
    display(state);display(pd.DataFrame(items))
    evidence.update(campaign=state,items=items)
    if params.execute_write and state["status"]!="COMPLETED":
        report(NOTEBOOK_ID,evidence,status="FAIL",generation="v3")
        raise RuntimeError("Campanha não completou: "+state["status"]+"; consulte os erros dos jobs persistidos")
else:
    evidence["training"]="NOT_EXECUTED: escolha campanha existente ou habilite escrita"
'''
    emit("04_treinamento_individual","Experimento individual e baseline",[
        ("1. Selecionar snapshot, algoritmo ridge/dummy e alpha. Uma campanha com um item mantém idempotência e execução independente do kernel.",'''from src.data.journey import extract
_,snapshot=extract(cfg);display(snapshot)
scopes=call(cfg,"GET","/v1/audit/scopes")
display(pd.DataFrame(scopes))
model_keys=[params.model_name]
if params.model_name=="planilha-turmas-demo":
    model_keys=[scopes[0]["model_key"]]
display({"model":params.model_name,"algorithm":params.algorithm,"alpha":params.alpha,"baseline":"DummyRegressor mean"})
'''),("2. Submeter e acompanhar treino real opt-in; candidato não é promovido.",training),
        ("3. Comparar métricas, prova de download/checksum e reload feitas pelo job. Se executado, o resultado deve ter três evidências de arquivo por modelo.",'''for item in evidence.get("items",[]):
    if item["status"]=="COMPLETED":
        display(item["result"])
        assert len(item["result"]["storage_evidence"])==3
        display(Markdown(f"[Run]({cfg.ui}/#/experiments/{item['result']['experiment_id']}/runs/{item['mlflow_run_id']})"))
display_locations(cfg,evidence.get("items",[]))
''')])
    emit("05_treinamento_campanha","Campanhas persistentes de modelos",[
        ("1. Catálogo e orçamento. Chaves hi.pt.demanda representam períodos cadastrados DEMO; não são fontes institucionais. Default: três modelos, máximo de dois processos.",'''display(pd.DataFrame(call(cfg,"GET","/v1/training/campaigns")))
from src.data.journey import extract
_,snapshot=extract(cfg,snapshot_id=str(params.snapshot_id) if params.snapshot_id else None)
display(snapshot)
scopes=call(cfg,"GET","/v1/audit/scopes")
display(pd.DataFrame(scopes))
if params.model_count>len(scopes):
    raise ValueError("O catálogo DEMO não possui esse número de séries distintas; use até "+str(len(scopes)))
model_keys=[s["model_key"] for s in scopes[:params.model_count]]
display({"model_count":len(model_keys),"max_parallel_jobs":params.parallel_jobs,"first_keys":model_keys[:5]})
'''),("2. Controle opt-in: pause/resume/cancel/retry-failed. Cancelamento é cooperativo; itens em execução concluem, pendentes são cancelados.",'''if params.campaign_action not in ("create","observe"):
    params.authorize()
    if not params.campaign_id: raise ValueError("campaign_id obrigatório")
    evidence["control"]=call(cfg,"POST",f"/v1/training/campaigns/{params.campaign_id}/{params.campaign_action}")
    display(evidence["control"])
'''),("3. Criar campanha somente quando campaign_action=create, ou observar o ID escolhido. Estado/checkpoints permanecem no PostgreSQL após fechar o notebook.",'''if params.campaign_action!="create":
    params=params.model_copy(update={"execute_write":False})
'''+training),
        ("4. Quantidades comprovadas e progresso. Treinos reais, versões e instâncias de serving são números distintos.",'''items=evidence.get("items",[])
display({"requested":len(items),"completed":sum(i["status"]=="COMPLETED" for i in items),"registered_versions":sum(bool(i["model_version"]) for i in items),"automatically_promoted":0,"new_HTTP_servers":0})
display_locations(cfg,items)
''')])
    emit("06_avaliacao_comparativa","Comparar runs e escolher candidato",[
        ("1. Filtrar por snapshot explícito. Compare apenas a mesma janela; baseline e métricas são demonstrativos.",'''from src.workbench.operations_sdk import comparison
records=comparison(cfg,str(params.snapshot_id) if params.snapshot_id else "",limit=500)
table=pd.DataFrame(records);display(table)
evidence["runs"]=records
'''),("2. Eleger candidato por menor MAE dentro de um único snapshot/janela, sem aprovar ou promover.",'''if not table.empty and "mae" in table and params.snapshot_id:
    comparable=table.dropna(subset=["snapshot_id","model_key","evaluation_window","target","dataset_sha256"])
    groups=comparable.groupby(["snapshot_id","model_key","evaluation_window","target","dataset_sha256"])
    candidates=[g.sort_values("mae").iloc[0].to_dict() for _,g in groups if g.mae.notna().any()]
    display(pd.DataFrame(candidates));evidence["candidates"]=candidates
else:
    display({"candidate":"NOT_EVALUATED","reason":"Selecione snapshot e runs com mesma janela"})
evidence["promotion"]="NOT_EXECUTED"
''')])
    emit("07_registry_governanca","Revisão humana, aprovação e rollback",[
        ("1. Modelos/versões e pedidos de revisão. Registro é candidato; aprovação exige token separado de operador e versão explícita.",'''import mlflow
mlflow.set_tracking_uri(cfg.tracking);client=mlflow.MlflowClient()
from urllib.parse import urlencode
catalog=call(cfg,"GET","/v1/governance/models?"+urlencode(dict(prefix=params.registry_prefix,page_token=params.registry_page_token,limit=100)))
display(pd.DataFrame(catalog["items"]));display({"next_page_token":catalog["next_page_token"]})
versions=client.search_model_versions("name='"+params.model_name+"'",max_results=100)
display(pd.DataFrame([dict(model=v.name,version=v.version,run_id=v.run_id,tags=v.tags) for v in versions]))
display(pd.DataFrame(call(cfg,"GET","/v1/governance/requests")))
'''),("2. Inspecionar artefatos e proveniência da versão selecionada. Esperado: hashes iguais; nenhuma aprovação implícita.",'''if params.model_version:
    from src.operations.training import trace_for
    from src.workbench.verification import verify_model_storage
    trace=trace_for(client,client.get_model_version(params.model_name,params.model_version))
    evidence["candidate"]=trace;evidence["storage"]=verify_model_storage(trace)
    display(trace);display(pd.DataFrame(evidence["storage"]))
'''),("3. Ação opt-in: solicitar revisão ou decidir pedido identificado. APPROVE/REVOKE/ROLLBACK requerem justificativa; reviewer vem da credencial, não do texto digitado.",'''if params.governance_action!="read":
    params.authorize()
    if params.governance_action=="request":
        if not params.model_version or len(params.reason)<8: raise ValueError("Versão e justificativa obrigatórias")
        evidence["review"]=call(cfg,"POST","/v1/governance/requests",dict(model_name=params.model_name,model_version=params.model_version,
            action=params.review_action,reason=params.reason,requested_by=params.requester))
    else:
        if not params.approval_id: raise ValueError("approval_id obrigatório")
        evidence["review"]=call(cfg,"POST",f"/v1/governance/requests/{params.approval_id}/review",
            dict(approve=params.governance_action=="approve",confirm="REVIEW_EXPLICIT_VERSION"),operator=True)
    display(evidence["review"])
else:
    evidence["review"]="NOT_EXECUTED: leitura"
''')])
    emit("08_auditoria_lineage","Navegar e verificar lineage",[
        ("1. Escolha proposta, run, modelo+versão, snapshot ou campanha; paginação limita o grafo retornado.",'''from src.workbench.lineage_review import inspect_graph
external_id=params.external_id or (str(params.proposal_id) if params.proposal_id else "")
if not external_id: raise ValueError("Informe external_id ou proposal_id")
evidence=inspect_graph(cfg,params.lineage_kind,external_id,params.model_version)
display(pd.DataFrame(evidence["nodes"]));display(pd.DataFrame(evidence["edges"]))
'''),("2. Grafo e verificações reais. VERIFIED exige presença/proveniência; MISSING/MISMATCH bloqueiam confiança; legado continua identificado.",'''from IPython.display import HTML
from src.workbench.lineage_review import render_graph
display(HTML(render_graph(evidence)))
display(pd.DataFrame(evidence["checks"]))
reconciled=audit(cfg,params.lineage_kind,external_id,params.model_version)
display(reconciled)
inventory_rows=call(cfg,"GET","/v1/audit/inventory?limit=500")
display(pd.DataFrame(inventory_rows))
display(export_session(reconciled,inventory_rows))
''')])
    emit("09_reset_total_ambiente_poc","Preparar e auditar reset externo",[
        ("1. Selecionar modo e rebootstrap, sem executar exclusão. O controlador do host encerra o kernel em factory-reset; Run All é sempre somente leitura.",'''from src.workbench.reset_review import review_plan
evidence=review_plan(params)
display(evidence["commands"])
display({"state":evidence["state"],"destructive_execution":"NOT_EXECUTED"})
'''),("2. Inventário, impacto, arquivos preservados e resultado. Plano expirado deve ser recriado no terminal; nunca execute comando antigo sem novo preview.",'''display(evidence.get("inventory",{}))
display(evidence.get("protected_files",{}))
display(evidence.get("result",{}))
''')])
