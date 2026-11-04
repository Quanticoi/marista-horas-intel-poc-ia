"""Human navigation and export; read-only HTTP/SQL checks never train models."""
import csv
import io
import json
import os
from pathlib import Path
from urllib.parse import quote,urlencode
from uuid import uuid4
from src.common.lineage import utcnow,reject_sensitive
from src.workbench.operations_sdk import call,write_report_file
from src.workbench.sdk import source_version


def where_to_check(cfg,result):
    catalog=result.get('catalog') or {}
    name=result.get('model_name') or result.get('model_key')
    version=str(result['model_version']);run=result['run_id']
    eid=result.get('experiment_id') or catalog.get('experiment_id')
    return [dict(destination='Modelo DEMO',label=catalog.get('model_display_name',name),reference=f'{name}/{version}'),
        dict(destination='Experimento',label=catalog.get('experiment_name',cfg.experiment),reference=f'{cfg.ui}/#/experiments/{eid}'),
        dict(destination='Run',label=catalog.get('run_name',run[:8]),reference=f'{cfg.ui}/#/experiments/{eid}/runs/{run}'),
        dict(destination='Registry',label=f'{name} • versão {version}',reference=f'{cfg.ui}/#/models/{quote(name,safe="")}/versions/{version}'),
        dict(destination='RustFS',label='Console • catálogo e arquivos reais',reference='http://localhost:9001'),
        dict(destination='Manifest',label='Índice imutável HI-LINEAGE/1.1' if catalog else 'Legado: catálogo 1.1 não aplicável',reference=catalog.get('manifest_uri')),
        *[dict(destination='Arquivo RustFS',label=f['key'].rsplit('/',1)[-1],reference=f"s3://{f['bucket']}/{f['key']}") for f in result.get('storage_evidence',[])],
        dict(destination='PostgreSQL',label='planejamento_db.planning.v_model_inventory',reference='SELECT * FROM planning.v_model_inventory WHERE model_key=:model_key AND model_version=:version'),
        dict(destination='API GET Bearer',label='Auditoria da versão',reference='http://localhost:8000/v1/audit/model?'+urlencode(dict(model_key=name,version=version))),
        dict(destination='Dashboard',label='Filtrar model_key/run_id/campaign_id/correlation_id',reference='http://localhost:8088'),
        dict(destination='Run ID completo',label=run[:8],reference=run)]


def display_locations(cfg,items):
    import pandas as pd
    from IPython.display import display,Markdown
    display(Markdown('### Onde conferir'))
    for item in items:
        result=item.get('result',item)
        if not result.get('model_version'):
            continue
        table=where_to_check(cfg,result)
        display(pd.DataFrame(table))
        for row in table:
            if str(row['reference']).startswith('http'):
                display(Markdown(f"[{row['destination']}]({row['reference']})"))


def audit(cfg,kind,external_id,version=''):
    if kind=='proposal':
        return call(cfg,'GET',f'/v1/audit/proposal/{external_id}')
    if kind=='model':
        return call(cfg,'GET','/v1/audit/model?'+urlencode(dict(model_key=external_id,version=version)))
    field={'run':'run_id','snapshot':'snapshot_id','campaign':'campaign_id'}[kind]
    return dict(inventory=call(cfg,'GET','/v1/audit/inventory?'+urlencode({field:external_id,'limit':500})))


def export_session(evidence,inventory_rows,manual_checks=None):
    identifier=str(uuid4())
    document=dict(manual_session_id=identifier,executed_at_utc=utcnow(),git_commit=os.getenv('CODE_VERSION','uncommitted'),
        code_version=source_version(),environment='poc',source_type='DEMO',evidence=evidence,
        manual_checks=manual_checks or {k:'NOT_CHECKED' for k in ('MLflow UI','RustFS UI','PostgreSQL','Dashboard')},
        limitations=['Dados DEMO; contrato provisório; observações manuais não são inferidas de testes HTTP'])
    reject_sensitive(document)
    if any(v not in ('PASS','FAIL','NOT_CHECKED') for v in document['manual_checks'].values()):
        raise ValueError('Manual observations must be PASS, FAIL or NOT_CHECKED')
    root=Path('/reports/v3');root.mkdir(parents=True,exist_ok=True)
    if root.stat().st_uid==os.geteuid():
        root.chmod(0o777)  # Shared report mount: tools and Jupyter run as different UIDs.
    path=root/f'manual-session-{identifier}.json'
    write_report_file(path,json.dumps(document,default=str,ensure_ascii=False,indent=2))
    fields=('model_key','model_version','model_display_name','run_id','snapshot_id','manifest_uri','artifact_sha256')
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(inventory_rows)
    write_report_file(path.with_suffix('.csv'),stream.getvalue())
    ui=os.getenv('MLFLOW_UI_BASE_URL','http://localhost:5000').rstrip('/')
    links=['\n\n| Modelo DEMO / versão | Run completo | Registry | Manifest |','|---|---|---|---|']
    for item in inventory_rows:
        name=item['model_key'];version=item['model_version'];run=item['run_id']
        links.append(f"| {name} / {version} | [{run}]({ui}/#/experiments/{item.get('experiment_id')}/runs/{run}) | [Abrir versão]({ui}/#/models/{quote(name,safe='')}/versions/{version}) | {item.get('manifest_uri')} |")
    objects=[dict(f,model_key=m['model_key'],run_id=m['run_id'],model_version=m['model_version'])
        for m in evidence.get('models',[evidence]) for f in m.get('files',[])]
    if objects:
        stream=io.StringIO()
        writer=csv.DictWriter(stream,fieldnames=('bucket','key','bytes','sha256','model_key','model_version','run_id'),extrasaction='ignore')
        writer.writeheader();writer.writerows(objects)
        write_report_file(path.with_suffix('.objects.csv'),stream.getvalue())
        links.append(f"\n[Objetos reais: chave, bytes e SHA256]({path.with_suffix('.objects.csv').name})")
    write_report_file(path.with_suffix('.md'),f"# Sessão manual {identifier}\n\n{document['executed_at_utc']} • DEMO\n\n[JSON]({path.name}) · [Inventário CSV]({path.with_suffix('.csv').name})\n\n"+
        '\n'.join(f'- {k}: {v}' for k,v in document['manual_checks'].items())+
        '\n'.join(links)+'\n\n[MLflow](http://localhost:5000) · [RustFS](http://localhost:9001) · [API](http://localhost:8000/docs) · [Dashboard](http://localhost:8088)\n')
    return str(path)
