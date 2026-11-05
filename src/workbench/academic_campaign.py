"""Restartable Workbench-local campaigns. SQL checkpoints; no Celery or application POST."""
import json
import os
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from uuid import UUID,uuid4,uuid5,NAMESPACE_URL
import mlflow
from sqlalchemy import text
from src.persistence.db import engine,rows
from src.simulation.academic import digest
from src.workbench.academic_data import load
from src.workbench.academic_training import fit_model
from src.workbench.metrics_v4 import aggregate,catalog,profile
from src.common.lineage import put_manifest
from src.common.logging import event


def require_workbench():
    if os.getenv('WORKBENCH_EXECUTOR')!='1' or not Path('/opt/conda').is_dir():
        raise RuntimeError('Use the Jupyter Workbench container, never the application worker')


def checkpoint(campaign,key,**changes):
    allowed={'state','attempt','run_id','result'}
    if not changes or set(changes)-allowed:
        raise ValueError('Invalid checkpoint fields')
    params=dict(campaign=campaign,key=key)
    assignments=[]
    for name,value in changes.items():
        params[name]=json.dumps(value) if name=='result' else value
        assignments.append(name+'='+('CAST(:result AS jsonb)' if name=='result' else ':'+name))
    with engine().begin() as con:
        con.execute(text('UPDATE planning.workbench_models SET '+','.join(assignments)+' WHERE campaign_id=:campaign AND model_key=:key'),params)


def tracked_result(client,version):
    from src.workbench.verification import verify_model_storage
    with tempfile.TemporaryDirectory() as directory:
        filename=client.download_artifacts(version.run_id,'training_result.json',directory)
        result=json.loads(Path(filename).read_text())
    if result['model_name']!=version.name or str(result['model_version'])!=str(version.version):
        raise ValueError('Registry recovery identity mismatch')
    result['storage_evidence']=verify_model_storage(result)
    client.set_terminated(version.run_id,'FINISHED')
    result['validation_status']='VALIDATED' if result['evaluations'] else 'TRAINED_NOT_EVALUATED'
    return result


def run_item(frame,manifest,item,campaign,batch_id,batch_run,eid):
    key=item['model_key'];client=mlflow.MlflowClient()
    saved=rows('SELECT * FROM planning.workbench_models WHERE campaign_id=:c AND model_key=:m',{'c':campaign,'m':key})[0]
    if saved['state']=='COMPLETED':
        return saved['result']
    if saved['attempt']>=3:
        raise ValueError('RETRY_EXHAUSTED: use a new intentional campaign after diagnosis')
    attempt=saved['attempt']+1
    checkpoint(campaign,key,state='RUNNING',attempt=attempt)
    try:
        recovered=None
        if saved['run_id']:
            token=None
            while True:
                page=client.search_model_versions("name = '"+key+"'",max_results=100,page_token=token)
                versions=[v for v in page if v.run_id==saved['run_id']]
                if versions:
                    if len(versions)!=1:
                        raise ValueError('Ambiguous Registry recovery')
                    recovered=tracked_result(client,versions[0]);break
                token=page.token
                if not token:
                    break
            if recovered is None:
                client.set_terminated(saved['run_id'],'KILLED')
        if recovered is None:
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            active=client.create_run(eid,tags={'mlflow.runName':f'{key}__{item["algorithm"]}__{stamp}__a{attempt}',
                                               'run_type':'MODEL','campaign_id':campaign,'batch_id':batch_id,
                                               'mlflow.parentRunId':batch_run})
            checkpoint(campaign,key,run_id=active.info.run_id)
            result=fit_model(frame,manifest,item,campaign,batch_id,batch_run,eid,active.info.run_id,attempt)
        else:
            result=recovered
        manifest_key=f'lineage/poc/planilha-turmas/v4/models/{key}/versions/v{int(result["model_version"]):04}/manifest.json'
        result['manifest']=put_manifest(manifest_key,dict(result,status_at_creation='RECORDED'))
        checkpoint(campaign,key,state='COMPLETED',result=result)
        event('workbench','model completed',correlation_id=campaign,model_key=key,run_id=result['run_id'])
        return result
    except Exception as error:
        checkpoint(campaign,key,state='FAILED',result={'error_type':type(error).__name__})
        current=rows('SELECT run_id FROM planning.workbench_models WHERE campaign_id=:c AND model_key=:m',{'c':campaign,'m':key})[0]['run_id']
        if current:
            try:
                client.set_terminated(current,'FAILED')
            except Exception:
                pass
        event('workbench','model failed',level='ERROR',correlation_id=campaign,model_key=key,error_type=type(error).__name__)
        raise


def log_summary(client,run_id,results,requested,selected):
    metrics=aggregate([record for result in results for record in result['evaluations']],selected)
    document=dict(requested=requested,completed=len(results),failed=requested-len(results),
                  not_evaluated=sum(not r['evaluations'] for r in results),
                  quality_eligible=sum(r['validation_status']=='VALIDATED' for r in results),
                  aggregation=metrics,models=results)
    client.log_metric(run_id,'completed',len(results))
    client.log_metric(run_id,'requested',requested)
    client.log_metric(run_id,'failed',requested-len(results))
    for index,group in enumerate(metrics):
        for metric,value in group['metrics'].items():
            if value['status']=='EVALUATED':
                client.log_metric(run_id,f'group{index}.{group["comparison"]["target_name"]}.{metric}',value['value'])
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'campaign_summary.json'
        path.write_text(json.dumps(document,ensure_ascii=False,indent=2))
        client.log_artifact(run_id,str(path))
    return document


def execute(snapshot_id,request_key,items=None,batch_size=2,max_workers=1,metric_profile='forecast_extended'):
    require_workbench()
    UUID(str(snapshot_id))
    if not request_key or len(request_key)>160 or not 1<=batch_size<=20 or not 1<=max_workers<=2:
        raise ValueError('Invalid campaign key, batch size or concurrency (1..2)')
    items=items or [dict(course_code='2248',algorithm='ridge'),dict(course_code='2348',algorithm='dummy'),dict(course_code='2287',algorithm='ridge')]
    selected=profile(metric_profile)['selected']
    if not selected:
        raise ValueError('Select forecast metrics')
    normalized=[]
    for item in items:
        course=str(item['course_code']);algorithm=item['algorithm']
        if not course.isdigit() or algorithm not in ('ridge','dummy'):
            raise ValueError('Invalid course/algorithm')
        normalized.append(dict(course_code=course,algorithm=algorithm,model_key=f'hi.demo.v4.c{course}.components',metric_profile=metric_profile))
    if len({i['model_key'] for i in normalized})!=len(normalized):
        raise ValueError('One explicit algorithm per model identity/campaign; use a new campaign to compare versions')
    frame,manifest=load(snapshot_id)
    if any(i['course_code'] not in set(frame.course_code) for i in normalized):
        raise ValueError('Course scope absent from SQL snapshot')
    tracking=os.environ['MLFLOW_TRACKING_URI']
    if not tracking.startswith(('http://','https://')):
        raise ValueError('Remote tracking required; no local fallback')
    mlflow.set_tracking_uri(tracking);mlflow.set_registry_uri(tracking)
    client=mlflow.MlflowClient()
    client.search_experiments(max_results=1)
    request=dict(snapshot_id=str(snapshot_id),dataset_sha256=manifest['dataset_sha256'],items=normalized,
                 batch_size=batch_size,max_workers=max_workers,metric_profile=metric_profile)
    with engine().begin() as con:
        con.execute(text('SELECT pg_advisory_xact_lock(hashtext(:key))'),{'key':'workbench:'+request_key})
        prior=con.execute(text('SELECT * FROM planning.workbench_campaigns WHERE request_key=:key'),{'key':request_key}).mappings().first()
        if prior and prior['request_hash']!=digest(request):
            raise ValueError('Idempotency key reused with different campaign configuration')
        if prior:
            campaign=str(prior['campaign_id'])
        else:
            campaign=str(uuid4())
            con.execute(text("""INSERT INTO planning.workbench_campaigns(campaign_id,request_key,request_hash,request,status)
                VALUES (:id,:key,:hash,CAST(:request AS jsonb),'PENDING')"""),
                dict(id=campaign,key=request_key,hash=digest(request),request=json.dumps(request)))
            for item in normalized:
                con.execute(text("INSERT INTO planning.workbench_models(campaign_id,model_key,state) VALUES (:c,:m,'PENDING')"),
                            {'c':campaign,'m':item['model_key']})
    with engine().connect() as lock:
        acquired=lock.execute(text('SELECT pg_try_advisory_lock(hashtext(:key))'),{'key':'workbench:'+campaign}).scalar_one()
        lock.commit()
        if not acquired:
            raise ValueError('Campaign already running in another Workbench process')
        try:
            row=rows('SELECT * FROM planning.workbench_campaigns WHERE campaign_id=:c',{'c':campaign})[0]
            if row['status']=='COMPLETED':
                return row['result']
            name='HI/POC/PlanilhaTurmas/academic-components/'+manifest['target']
            exp=client.get_experiment_by_name(name)
            eid=exp.experiment_id if exp else client.create_experiment(name)
            if not client.get_experiment(eid).artifact_location.startswith('mlflow-artifacts:'):
                raise ValueError('Proxy artifact experiment required')
            # Prove tracking metadata AND artifact roundtrip before any fit.
            with mlflow.start_run(experiment_id=eid,run_name='Workbench dependency diagnostic',
                                  tags={'purpose':'dependency-diagnostic','campaign_id':campaign}) as diagnostic:
                with tempfile.TemporaryDirectory() as directory:
                    probe=Path(directory)/'workbench-probe.txt';probe.write_text(campaign)
                    mlflow.log_artifact(str(probe),'diagnostics')
                    output=Path(directory)/'readback';output.mkdir()
                    restored=client.download_artifacts(diagnostic.info.run_id,'diagnostics/workbench-probe.txt',str(output))
                    if Path(restored).read_text()!=campaign:
                        raise ValueError('MLflow artifact roundtrip failed before training')
            parent=row['run_id'] or client.create_run(eid,tags={'mlflow.runName':'POC 2024.2 • Demanda acadêmica • Lote piloto',
                'run_type':'CAMPAIGN','campaign_id':campaign,'snapshot_id':str(snapshot_id),'data_class':'SYNTHETIC_HISTORY'}).info.run_id
            with engine().begin() as con:
                con.execute(text("UPDATE planning.workbench_campaigns SET status='RUNNING',run_id=:run WHERE campaign_id=:id"),{'run':parent,'id':campaign})
            results=[];failed=[]
            for offset in range(0,len(normalized),batch_size):
                members=normalized[offset:offset+batch_size]
                bid=str(uuid5(NAMESPACE_URL,campaign+':batch:'+str(offset//batch_size)))
                batch=client.create_run(eid,tags={'mlflow.runName':f'Lote {offset//batch_size+1} • {len(members)} modelos',
                    'run_type':'BATCH','campaign_id':campaign,'batch_id':bid,'parent_run_id':parent,'mlflow.parentRunId':parent}).info.run_id
                batch_results=[]
                with ThreadPoolExecutor(max_workers=max_workers) as pool:
                    futures=[pool.submit(run_item,frame,manifest,item,campaign,bid,batch,eid) for item in members]
                    for item,future in zip(members,futures):
                        try:
                            result=future.result();results.append(result);batch_results.append(result)
                        except Exception as error:
                            failed.append(dict(model_key=item['model_key'],error_type=type(error).__name__))
                log_summary(client,batch,batch_results,len(members),selected)
                client.set_terminated(batch,'FINISHED' if len(batch_results)==len(members) else 'FAILED')
                log_summary(client,parent,results,offset+len(members),selected)
            summary=log_summary(client,parent,results,len(normalized),selected)
            summary.update(campaign_id=campaign,run_id=parent,experiment_id=eid,failures=failed,
                           status='COMPLETED' if not failed else 'PARTIAL',executor='JUPYTER_WORKBENCH',
                           metric_catalog=catalog(),snapshot_id=str(snapshot_id))
            client.set_terminated(parent,'FINISHED' if not failed else 'FAILED')
            with engine().begin() as con:
                con.execute(text("UPDATE planning.workbench_campaigns SET status=:status,result=CAST(:result AS jsonb),updated_at=now() WHERE campaign_id=:id"),
                    dict(id=campaign,status=summary['status'],result=json.dumps(summary)))
            return summary
        finally:
            lock.execute(text('SELECT pg_advisory_unlock(hashtext(:key))'),{'key':'workbench:'+campaign})
            lock.commit()


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--snapshot-id',required=True)
    parser.add_argument('--request-key',required=True)
    parser.add_argument('--output',type=Path,default=Path('/reports/v4/training-evidence.json'))
    args=parser.parse_args()
    result=execute(args.snapshot_id,args.request_key)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('campaign_id','status','completed','failed','failures')},indent=2))
    if result['status']!='COMPLETED':
        raise SystemExit(2)


if __name__=='__main__':
    main()
