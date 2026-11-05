"""Application simulator uses authenticated HTTP only, never SQL/MLflow/storage SDKs."""
import hashlib
import json
import os
import time
from pathlib import Path
import httpx
import pandas as pd
from src.api.academic_contract import ApplicationView

CONTEXT=Path('/workspace/reports/v4-context.json')


def context():
    return json.loads(CONTEXT.read_text()) if CONTEXT.exists() else {}


def save_context(**updates):
    value=dict(context(),**updates)
    CONTEXT.parent.mkdir(parents=True,exist_ok=True)
    temporary=CONTEXT.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2))
    temporary.replace(CONTEXT)
    return value


def call(method,path,body=None,key=None,operator=False):
    token=os.environ['OPERATOR_TOKEN' if operator else 'API_TOKEN']
    headers={'Authorization':'Bearer '+token}
    if key:
        headers['Idempotency-Key']=key
    for attempt in range(3 if method=='GET' else 1):
        try:
            response=httpx.request(method,os.environ['API_URI']+path,json=body,headers=headers,timeout=30)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as error:
            raise RuntimeError(f'API {path}: HTTP {error.response.status_code}; correlation_id={error.response.headers.get("X-Correlation-ID","unknown")}') from None
        except httpx.TransportError:
            if attempt==2 or method!='GET':
                raise RuntimeError('API indisponível; docker compose logs --tail 100 api inference worker') from None
            time.sleep(1)


def select_proposal(explicit=None):
    selection=proposal_selection(explicit)
    if selection['proposal_id']:
        return selection['proposal_id']
    raise ValueError(selection['message'])


def proposal_selection(explicit=None):
    """Resolve the active campaign via HTTP; missing generation is a UI state."""
    saved=context()
    candidate=explicit or os.getenv('PROPOSAL_ID') or saved.get('proposal_id')
    if candidate:
        return dict(status='SELECTED',proposal_id=candidate,choices=[],message='Proposta selecionada pelo contexto ou identificador explícito.')
    choices=call('GET','/v2/proposals?limit=500')
    matching=choices
    if saved.get('campaign_id'):
        from urllib.parse import urlencode
        matching=call('GET','/v2/proposals?'+urlencode(dict(limit=500,campaign_id=saved['campaign_id'])))
    if len(matching)==1:
        selected=str(matching[0]['proposal_id'])
        save_context(proposal_id=selected)
        return dict(status='SELECTED',proposal_id=selected,choices=choices,message='Proposta recuperada automaticamente pela API.')
    if saved.get('campaign_id') and not matching:
        message=('A campanha atual ainda não possui proposta concluída. Treinar não gera a Planilha Turmas. '
                 'No 07, revise e habilite APPROVE_DEMO=True. No 08, habilite DEPLOY_DEMO=True e GENERATE=True '
                 'e execute até COMPLETED. Depois reexecute o 09. Você também pode consultar explicitamente uma proposta anterior abaixo.')
        status='AWAITING_GENERATION'
    elif not matching:
        message='Nenhuma proposta concluída está disponível. Conclua a revisão no 07 e a geração no 08 antes de consultar o 09.'
        status='EMPTY'
    else:
        message='Há mais de uma proposta disponível. Escolha abaixo qual deseja consultar.'
        status='CHOICE_REQUIRED'
    return dict(status=status,proposal_id=None,choices=choices if not matching else matching,message=message)


def proposal_picker(selection):
    """Explicit historical selection; no training, approval or generation side effects."""
    import ipywidgets as widgets
    from IPython.display import display,Markdown,clear_output
    display(Markdown('**'+selection['message']+'**\n\n'
        '[Abrir 07 — governança](07_governanca_registry.ipynb) · '
        '[Abrir 08 — geração](08_publicacao_inferencia.ipynb)'))
    if not selection['choices']:
        return None
    choices=widgets.Dropdown(description='Proposta',options=[('Selecione uma proposta',None)]+[
        (f"{r['cycle_code']} | {r['generated_at']} | {r['proposal_id']}",str(r['proposal_id'])) for r in selection['choices']],
        layout=widgets.Layout(width='95%'))
    button=widgets.Button(description='Selecionar para consulta',disabled=True)
    output=widgets.Output()
    choices.observe(lambda change:setattr(button,'disabled',change['new'] is None),names='value')
    def selected(_):
        with output:
            clear_output(wait=True)
            # Check the selected document before persisting its identity.
            document=fetch(choices.value)
            save_context(proposal_id=document['proposal_id'])
            display(Markdown('Proposta selecionada. **Reexecute as células do notebook** para carregar a tabela e a auditoria.'))
    button.on_click(selected)
    display(widgets.VBox([choices,button,output]))
    return choices


def fetch(proposal_id,filters=None,page_size=30):
    from urllib.parse import urlencode
    records=[];ids=set();offset=0;identity=None
    for _ in range(1000):
        query=urlencode(dict(filters or {},limit=page_size,offset=offset))
        page=call('GET',f'/v2/proposals/{proposal_id}/application-view?'+query)
        ApplicationView.model_validate(page)
        body={k:v for k,v in page.items() if k!='payload_sha256'}
        digest=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()
        if digest!=page['payload_sha256'] or page['offset']!=offset or page['limit']!=page_size or page['proposal_id']!=str(proposal_id):
            raise ValueError('Contrato HTTP: identidade, hash ou paginação divergente')
        current=(page['proposal_sha256'],page['total_rows'],page['proposal_revision'])
        if identity is not None and current!=identity:
            raise ValueError('Proposal changed across pages')
        identity=current
        for offer in page['offers']:
            if offer['offer_id'] in ids:
                raise ValueError('Contrato HTTP: oferta duplicada entre páginas')
            ids.add(offer['offer_id']);records.append(offer)
        offset+=len(page['offers'])
        if offset==page['total_rows']:
            return dict(page,offers=records)
        if not page['offers'] or offset>page['total_rows']:
            raise ValueError('Contrato HTTP: paginação incompleta')
    raise ValueError('Pagination limit exceeded')


def table(offers):
    return pd.DataFrame([dict(offer_id=o['offer_id'],Estabelecimento=o['academic']['establishment'],Escola=o['academic']['school'],
        Curso=o['academic']['course_code'],Grade=o['academic']['curriculum_code'],Ingresso=o['academic']['cohort_ingress'],
        Coorte=o['academic']['cohort_id'],Período=o['academic']['period'],Turno=o['academic']['shift'],
        Disciplina=o['academic']['discipline_code'],Descrição=o['academic']['discipline_name'],
        Regular=o['demand']['regular']['value'],Dependência=o['demand']['dependency']['value'],Eletiva=o['demand']['elective']['value'],
        Total_previsto=o['demand']['estimated_total'],Atividades=len(o['activities']),Unificação=o['unification']['status'],Status=o['status']) for o in offers])


def explorer(proposal_id,payload):
    import ipywidgets as widgets
    from IPython.display import display,clear_output,Markdown
    keys=['school','course_code','curriculum_code','cohort_id','period','shift','discipline_code','offer_type']
    controls={k:widgets.Dropdown(description=k,options=[('Todos','')]+[(str(v),str(v)) for v in sorted(
        {o['academic'][k] for o in payload['offers'] if o['academic'][k] is not None},key=str)],layout=widgets.Layout(width='320px')) for k in keys}
    controls['status']=widgets.Dropdown(description='status',options=['']+sorted({o['status'] for o in payload['offers']}))
    controls['cycle_code']=widgets.Dropdown(description='ciclo',options=[payload['cycle_code']])
    output=widgets.Output();detail=widgets.Output();selector=widgets.Dropdown(description='Oferta',options=[])
    current={}
    def details(change=None):
        with detail:
            clear_output(wait=True)
            offer=current.get(selector.value)
            if offer:
                display(Markdown('**Atividades, composição e rastreabilidade recebidas pela API**'))
                display(pd.DataFrame(offer['activities']))
                display(offer['demand'])
                display(offer['lineage'],offer['unification'],offer['modulation'])
    def refresh(change=None):
        filters={k:c.value for k,c in controls.items() if c.value!=''}
        selected=fetch(proposal_id,filters)
        current.clear();current.update({o['offer_id']:o for o in selected['offers']})
        with output:
            clear_output(wait=True)
            display(table(selected['offers']))
        selector.options=[(o['academic']['course_code']+' / '+o['academic']['discipline_code'],o['offer_id']) for o in selected['offers']]
        details()
    for control in controls.values():
        control.observe(refresh,names='value')
    selector.observe(details,names='value')
    display(widgets.VBox([widgets.HBox(list(controls.values())[i:i+2]) for i in range(0,len(controls),2)]+[output,selector,detail]))
    refresh()
    return controls
