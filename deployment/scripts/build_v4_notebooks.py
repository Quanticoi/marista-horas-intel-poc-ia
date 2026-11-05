"""Build the twelve V4 source notebooks. Archive legacy sources once, never workspace edits."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'notebooks'


def notebook(name,title,sections):
    cells=[dict(cell_type='markdown',metadata={},source=f'# {title}\n\nPOC semissintética • contrato provisório • sem homologação acadêmica.\nExecute em kernel reiniciado, de cima para baixo. As credenciais vêm do ambiente.\n')]
    for heading,code in sections:
        cells.append(dict(cell_type='markdown',metadata={},source=heading))
        cells.append(dict(cell_type='code',metadata={},source=code,outputs=[],execution_count=None))
    cells.append(dict(cell_type='markdown',metadata={},source='**Onde conferir:** [MLflow](http://localhost:5000), [RustFS](http://localhost:9001), [API](http://localhost:8000/docs), [Logs](http://localhost:8088). Em falha: `docker compose logs --tail 100 api inference worker mlflow`.'))
    for index,cell in enumerate(cells):
        cell['id']=f'v4-{name[:2]}-{index}'
    body=dict(nbformat=4,nbformat_minor=5,cells=cells,metadata={'kernelspec':{'name':'pucpr','display_name':'PUCPR Python 3.12','language':'python'}})
    (DEST/(name+'.ipynb')).write_text(json.dumps(body,ensure_ascii=False,indent=1),encoding='utf-8')


SETUP='''import os, json
import pandas as pd
from IPython.display import display, Markdown
from src.workbench.application_client import call, context, save_context
'''


def build():
    notebook('00_ambiente','00 | Ambiente e dependências',[
        ('**Objetivo:** verificar SQL, MLflow e gravação/leitura real de artefato antes de treinar.\n**Entradas:** configuração Docker por ambiente. **Esperado:** todas as dependências PASS.',SETUP+'''
from uuid import uuid4
from src.workbench.journey_config import Settings
from src.workbench.journey_steps import dependencies
cfg=Settings.load()
status=dependencies(cfg,str(uuid4()),diagnostic_experiment='HI/POC/Diagnostics/V4')
display(pd.DataFrame(status))
assert all(r['status']=='PASS' for r in status), 'Dependência indisponível: interrompa antes do treinamento.'
'''),('**Executar:** consultar serviços e catálogos. **Resultado esperado:** versão e catálogos disponíveis, mesmo sem modelo carregado.','''
import mlflow
display({'SDK MLflow':mlflow.__version__,'Tracking interno':cfg.tracking,'UI navegador':cfg.ui,'Fonte SQL':'planejamento_db.planning — DEMO explícito'})
display(pd.DataFrame(call('GET','/v1/serving/models')))
display(call('GET','/v1/serving/runtime'))
''')])
    notebook('01_fontes_academicas','01 | Fontes acadêmicas e mapeamento',[
        ('**Objetivo:** importar ou inspecionar referências. **Entradas:** três planilhas em `/reference`, montadas somente para leitura. Nenhuma macro é executada. **Esperado:** 107 origens; 31 entidades/175 campos no arquivo real.',SETUP+'''
from pathlib import Path
from src.academic.importer import import_sources,persist
from src.persistence.db import rows
IMPORTAR=True
if IMPORTAR:
    imported=import_sources(Path('/reference'))
    persist(imported)
display(pd.DataFrame(rows('SELECT filename,sha256,byte_count FROM planning.academic_source_files ORDER BY filename')))
'''),('**Executar:** ler o que foi efetivamente persistido. **Resultado:** cursos distintos, fontes e divergências do contrato.','''
from src.workbench.academic_ui import references
source=pd.DataFrame(references())
assert len(source)==107
display(source.groupby(['course_code','shift']).size().rename('linhas').reset_index())
display(source[['course_code','curriculum_code','discipline_code','activity_type','division_label','source_row_number','status']].head(12))
display(rows('SELECT count(DISTINCT entity_name) AS entidades,count(*) AS campos FROM planning.academic_data_dictionary'))
''')])
    notebook('02_qualidade_dados','02 | Qualidade e grão acadêmico',[
        ('**Objetivo:** conferir chaves, atividades e quarentena. **Entradas:** referências SQL importadas. **Esperado:** 107 origens, 70 ofertas; 13 linhas em quarentena, preservadas.',SETUP+'''
from src.workbench.academic_ui import references
source=pd.DataFrame(references())
assert source.source_row_id.nunique()==107 and source.offer_id.nunique()==70
display(source.groupby('status').size().rename('linhas').reset_index())
display(source[['course_code','curriculum_code','period','discipline_code','shift']].isna().sum().rename('nulos'))
display(source[source.status=='QUARANTINED'][['course_code','discipline_code','source_row_number','issues']])
'''),('**Executar:** conferir P164 e P110A. **Resultado:** P164 tem teoria41 e práticas21+20; atividades não são alunos únicos.','''
p164=source[(source.course_code=='2248') & (source.discipline_code=='P164')]
assert p164.offer_id.nunique()==1 and sorted(p164.planned_students)==[20,21,41]
display(p164[['course_code','discipline_code','activity_type','division_label','planned_students','offered_seats']])
display(source[source.discipline_code=='P110A'][['course_code','curriculum_code','division_label','planned_students','source_row_number','status']])
''')])
    notebook('03_exploracao_demanda','03 | Histórico sintético por coorte e disciplina',[
        ('**Objetivo:** gerar histórico reproduzível condicionado à estrutura importada. **Entradas:** seed42, cenário baseline, ciclos2022-1 a2024-1; alvo2024-2. **Esperado:** snapshot SQL imutável, planejado separado de sintético.',SETUP+'''
from pathlib import Path
from src.academic.importer import import_sources
from src.simulation.academic import simulate
from src.simulation.store import save
SEED=42
CENARIO='baseline'
snapshot=simulate(import_sources(Path('/reference')),seed=SEED,profile=CENARIO)
save(snapshot)
save_context(snapshot_id=snapshot['snapshot_id'])
display({k:snapshot[k] for k in ('snapshot_id','dataset_sha256','scenario_id','history_window','target','data_completeness')})
'''),('**Executar:** observar regulares e adicionais por ciclo. **Resultado:** linha temporal SYNTHETIC_HISTORY; alvo futuro não entra no treino.','''
from src.workbench.academic_data import load
frame,_=load(snapshot['snapshot_id'])
display(frame.groupby(['course_code','split']).size().rename('observações').reset_index())
cyber=frame[(frame.course_code=='2287') & (frame.period==2)]
display(cyber[['cycle_code','cohort_id','discipline_code','regular','dependency','elective','split']].tail(12))
cyber.groupby('cycle_code')[['regular','dependency','elective']].mean().plot(marker='o',title='Médias DEMO por disciplina — não matrícula real')
''')])
    for number,multiple in ((4,False),(5,True)):
        name='04_treinamento_modelos' if number==4 else '05_campanhas_lotes'
        notebook(name,f'{number:02} | '+('Treinamento individual' if not multiple else 'Treinamento em lotes no Workbench'),[
            ('**Objetivo:** treinar no processo do Jupyter. **Entradas:** snapshot, escopo, algoritmo, lote e concorrência. `CAMPAIGN_MODE="NEW"` cria campanha e experimento novos a cada execução da célula de treino. Para retomar, escolha `RESUME` e informe a chave anterior. **Esperado:** prévia antes do fit.',SETUP+f'''
from src.workbench.academic_ui import snapshot_id,metric_controls,model_table
from src.workbench.academic_data import load,prepare
SNAPSHOT_ID=snapshot_id()
CAMPAIGN_MODE=os.getenv('V4_CAMPAIGN_MODE','NEW')
RESUME_REQUEST_KEY=os.getenv('V4_RESUME_REQUEST_KEY')  # Só usado no modo RESUME.
ITEMS={repr([dict(course_code='2248',algorithm='ridge'),dict(course_code='2348',algorithm='dummy'),dict(course_code='2287',algorithm='ridge')] if multiple else [dict(course_code='2248',algorithm='ridge')])}
BATCH_SIZE=2
MAX_WORKERS=1
RUN_TRAINING=os.getenv('V4_RUN_TRAINING','true').lower()=='true'
frame,manifest=load(SNAPSHOT_ID)
display(pd.DataFrame([dict(**item,train_rows=len(prepare(frame,item['course_code'])[0]),evaluation_rows=len(prepare(frame,item['course_code'])[1])) for item in ITEMS]))
display({{'recursos':'container Jupyter: limite3GiB; concorrência permitida1..2','targets':'regular,dependency,elective','avaliação':'holdout do último ciclo histórico; métricas sintéticas'}})
'''),('**Métricas:** selecione os checkboxes antes de executar a próxima célula. A seleção altera de fato o cálculo, o hash da configuração e o tracking. **Esperado:** seleção não vazia e compatível.','''
METRIC_PROFILE='forecast_extended'
metric_boxes=metric_controls(METRIC_PROFILE)
'''),('**Executar:** fit, predict, métricas, persistência proxy e Registry. **Resultado:** tabelas e links; nenhuma promoção automática.','''
from src.workbench.academic_campaign import execute
from uuid import uuid4
from IPython.display import Markdown
selected=[name for name,box in metric_boxes.items() if box.value]
if not selected:
    raise ValueError('Selecione pelo menos uma métrica.')
if RUN_TRAINING:
    if CAMPAIGN_MODE not in ('NEW','RESUME'):
        raise ValueError('CAMPAIGN_MODE deve ser NEW ou RESUME.')
    if CAMPAIGN_MODE=='RESUME' and not RESUME_REQUEST_KEY:
        raise ValueError('Informe RESUME_REQUEST_KEY da campanha anterior; não será criada outra silenciosamente.')
    REQUEST_KEY='v4-notebook-'+str(uuid4()) if CAMPAIGN_MODE=='NEW' else RESUME_REQUEST_KEY
    save_context(campaign_request_key=REQUEST_KEY,campaign_id=None,proposal_id=None)
    display({'modo':CAMPAIGN_MODE,'request_key':REQUEST_KEY,'retomada':'Guarde esta chave para RESUME em caso de interrupção.'})
    result=execute(SNAPSHOT_ID,REQUEST_KEY,items=ITEMS,batch_size=BATCH_SIZE,max_workers=MAX_WORKERS,metric_profile=METRIC_PROFILE,selected_metrics=selected,resume_only=CAMPAIGN_MODE=='RESUME')
    if result['status']!='COMPLETED':
        raise RuntimeError('Campanha parcial; consulte workbench_models e eventos por campaign_id.')
    save_context(campaign_id=result['campaign_id'],snapshot_id=SNAPSHOT_ID,proposal_id=None)
    ui=os.environ['MLFLOW_UI_BASE_URL'].rstrip('/')
    display(Markdown(f"[Abrir experimento {result['experiment_id']}]({ui}/#/experiments/{result['experiment_id']}) · [Abrir campanha]({ui}/#/experiments/{result['experiment_id']}/runs/{result['run_id']})"))
    display(pd.DataFrame([{k:result[k] for k in ('campaign_id','requested','completed','failed','quality_eligible')}]))
    display(model_table(result['models']))
    display(pd.DataFrame(result['aggregation']))
    pd.Series({m['course_code']:m['metrics'].get('regular.mae') for m in result['models']}).plot.bar(title='MAE regular — avaliação sintética',ylabel='estudantes')
else:
    display('NOT_EXECUTED: treinamento desabilitado explicitamente.')
''')])
    notebook('06_avaliacao_modelos','06 | Avaliação e limites científicos',[
        ('**Objetivo:** comparar com baseline e separar populações comparáveis. **Entrada:** campanha selecionada em04/05. **Esperado:** métricas por target/horizonte/split; não usar estes números como qualidade institucional.',SETUP+'''
from src.workbench.academic_ui import campaign_result,model_table
result=campaign_result()
display(model_table(result['models']))
metrics=[]
for model in result['models']:
    for key,value in model['metrics'].items():
        metrics.append(dict(curso=model['course_code'],métrica=key,valor=value))
display(pd.DataFrame(metrics))
'''),('**Executar:** conferir agregação e elegibilidade técnica. **Resultado:** RMSE calculado a partir dos erros combinados; sem aprovação automática.','''
display(pd.DataFrame(result['aggregation']))
display({'qualidade':'SYNTHETIC, avaliação temporal','aprovação':'requer decisão técnica explícita em07',
         'restrições':'capacidade oficial, PRIME e anuência de unificação ausentes; modulação REFERENCE_ONLY'})
''')])
    notebook('07_governanca_registry','07 | Revisão técnica de versões explícitas',[
        ('**Objetivo:** inspecionar candidatas e aprovar conscientemente. **Entradas:** campanha04/05; credencial de operador por ambiente. Por padrão apenas inspeciona. **Esperado:** estados distintos VALIDATED/APPROVED, sem homologação acadêmica.',SETUP+'''
from src.workbench.academic_ui import campaign_result,model_table
result=campaign_result()
display(model_table(result['models']))
APPROVE_DEMO=os.getenv('V4_APPROVE_DEMO','false').lower()=='true'
REASON='Revisão técnica explícita para demonstração POC sintética; sem homologação acadêmica.'
'''),('**Executar:** solicitação e revisão autenticadas. Para aprovar, defina `APPROVE_DEMO=True` e reexecute esta célula. **Resultado:** SQL e alias reconciliados; erros deixam o modelo bloqueado.','''
if APPROVE_DEMO:
    reviews=call('GET','/v1/governance/requests?limit=500')
    for model in result['models']:
        selector={k:model[k] for k in ('model_name','model_version')}
        current=[r for r in reviews if all(str(r[k])==str(v) for k,v in selector.items())]
        if any(r['status']=='APPROVED' for r in current):
            continue
        pending=[r for r in current if r['status'] in ('RECONCILING','REQUESTED') and r['action']=='APPROVE']
        request=pending[0] if pending else call('POST','/v1/governance/requests',dict(**selector,action='APPROVE',reason=REASON,requested_by='jupyter-poc-reviewer'))
        call('POST',f"/v1/governance/requests/{request['approval_id']}/review",dict(approve=True,confirm='REVIEW_EXPLICIT_VERSION'),operator=True)
else:
    display('INSPECT_ONLY: nenhuma aprovação executada.')
display(pd.DataFrame(call('GET','/v1/serving/models')))
''')])
    notebook('08_publicacao_inferencia','08 | Publicação e geração operacional',[
        ('**Objetivo:** disponibilizar versões aprovadas e gerar a proposta pela API. **Entradas:** campanha e decisões07. Por padrão consulta apenas; altere os controles explicitamente. **Esperado:** versão publicada distinta de residente.',SETUP+'''
from src.workbench.academic_ui import campaign_result
result=campaign_result()
DEPLOY_DEMO=os.getenv('V4_DEPLOY_DEMO','false').lower()=='true'
GENERATE=os.getenv('V4_GENERATE','false').lower()=='true'
GENERATION_KEY=os.getenv('V4_GENERATION_KEY','v4-proposal-'+result['campaign_id'])
selectors=[{k:m[k] for k in ('model_name','model_version')} for m in result['models']]
if DEPLOY_DEMO:
    for index,selector in enumerate(selectors):
        call('POST',f"/v1/serving/models/{selector['model_name']}/deploy",dict(**selector,policy='PRELOAD' if index==0 else 'LAZY'),
             key=f"v4-notebook-deploy-{selector['model_name']}-{selector['model_version']}",operator=True)
display(pd.DataFrame(call('GET','/v1/serving/models')))
display(call('GET','/v1/serving/runtime'))
'''),('**Executar:** geração HTTP, aguardando job persistido. **Resultado:**70 ofertas/107 origens, `proposal_id` salvo automaticamente para09. Mesma chave recupera; nova chave gera nova proposta, sem sobrescrever anteriores.','''
import time
if GENERATE:
    payload=dict(schema_version='poc-planilha-turmas-v2',snapshot_id=result['snapshot_id'],cycle_code='2024-2',proposal_revision=1,
                 model_selectors=selectors,requested_by='jupyter-poc')
    job=call('POST','/v2/proposals/generations',payload,key=GENERATION_KEY)
    for _ in range(90):
        job=call('GET',job['status_url'])
        if job['status'] in ('COMPLETED','FAILED'):
            break
        time.sleep(2)
    if job['status']!='COMPLETED':
        raise RuntimeError('Geração não concluída: '+str({k:job[k] for k in ('job_id','status','error_code')}))
    save_context(proposal_id=job['proposal_id'])
    display({k:job[k] for k in ('job_id','proposal_id','status','proposal_url')})
else:
    display('READ_ONLY: geração não solicitada. Use os controles após aprovação.')
''')])
    notebook('09_simulador_aplicacao','09 | Simulador da aplicação — somente HTTP',[
        ('**Objetivo:** consumir a proposta persistida sem SQL, treino ou SDK de storage. **Entradas:** contexto salvo em08; override explícito opcional. **Esperado:** paginação completa, hashes e schema válidos.',SETUP+'''
from src.workbench.application_client import select_proposal,fetch,table,explorer
PROPOSAL_ID=None  # Opcional: UUID escolhido na lista abaixo; contexto08 é automático.
display(pd.DataFrame(call('GET','/v2/proposals')))
proposal_id=select_proposal(PROPOSAL_ID)
payload=fetch(proposal_id,page_size=13)
display({'proposal_id':proposal_id,'ofertas':len(payload['offers']),'origens':sum(len(o['activities']) for o in payload['offers']),
         'schema':payload['schema_version'],'hash_proposta':payload['proposal_sha256'],'origem':'API HTTP → PostgreSQL'})
display(table(payload['offers']))
'''),('**Executar:** filtrar ciclo/escola/curso/matriz/coorte/período/turno/disciplina/tipo/status e abrir uma oferta. **Resultado:** cada filtro faz nova consulta HTTP; detalhe contém atividades, demanda e lineage.','''
controls=explorer(proposal_id,payload)
'''),('**Evidência:** conferir P164 exclusivamente pela API. **Resultado:** uma oferta, três atividades; 41 planejados não são 82 estudantes.','''
circuitos=fetch(proposal_id,{'course_code':'2248','discipline_code':'P164'})
assert len(circuitos['offers'])==1
offer=circuitos['offers'][0]
assert sorted(a['reference_planned_students'] for a in offer['activities'])==[20,21,41]
display(table(circuitos['offers']))
display(pd.DataFrame(offer['activities']))
''')])
    notebook('10_auditoria_lineage','10 | Auditoria reversa da proposta',[
        ('**Objetivo:** conferir proposta → inferência → versão → run → binário e snapshot. **Entrada:** contexto08 ou UUID explícito. **Esperado:** VERIFIED somente após confronto real de SQL/Registry/RustFS.',SETUP+'''
from src.workbench.application_client import select_proposal
proposal_id=select_proposal()
proof=call('GET',f'/v2/audit/proposals/{proposal_id}')
display({k:v for k,v in proof.items() if k not in ('models','inferences')})
display(pd.DataFrame(proof['models']))
display(pd.DataFrame(proof['inferences']))
assert proof['status']=='VERIFIED'
''')])
    notebook('11_reset_poc','11 | Limpar experimentos e preservar a origem',[
        ('**Objetivo:** preparar o reset seletivo. **Run All desta página NÃO executa exclusão.** O controlador no PowerShell para os serviços, limpa MLflow/RustFS/resultados derivados e preserva referências e histórico sintético SQL. Execute os comandos abaixo no terminal após conferir o plano; o próprio Jupyter será reiniciado.',SETUP+'''
display(pd.DataFrame(call('GET','/v2/proposals')))
display(pd.DataFrame(call('GET','/v1/serving/models')))
display({'destructive_execution':'NOT_EXECUTED','rebuild':'deployment/scripts/compose.ps1 rebuild',
         'preview':'python deployment/scripts/reset_poc.py preview --environment poc --project marista --mode reset-experiments',
         'execute':'python deployment/scripts/reset_poc.py execute --environment poc --project marista --plan-id UUID_DO_PLANO --execute',
         'confirmacao':'LIMPAR EXPERIMENTOS DA POC MARISTA',
         'preserva':'referências acadêmicas e carga sintética no PostgreSQL; arquivos locais e backups existentes',
         'remove':'experimentos/runs/Registry/traces, artefatos/versionamento RustFS, campanhas, inferências, aprovações, propostas e filas',
         'apos_reset':'MLflow sem runs/modelos; origem SQL com mesmos IDs e hashes; execute04/05 para nova campanha.'})
''')])


if __name__=='__main__':
    legacy=DEST/'legacy';legacy.mkdir(exist_ok=True)
    for path in DEST.glob('*.ipynb'):
        body=json.loads(path.read_text(encoding='utf-8'))
        if not body['cells'][0].get('id','').startswith('v4-'):
            target=legacy/path.name
            if target.exists() and target.read_bytes()!=path.read_bytes():
                raise ValueError('Legacy collision; inspect before replacing '+path.name)
            if not target.exists():
                path.replace(target)
    build()
    print('Generated twelve V4 notebooks; legacy sources preserved.')
