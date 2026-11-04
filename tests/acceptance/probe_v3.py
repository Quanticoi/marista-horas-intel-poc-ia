"""Container-side acceptance. Mutations strictly restricted to disposable project."""
import argparse
import json
import os
from pathlib import Path
from uuid import uuid4
import httpx
import mlflow
from src.common.settings import required
from src.common.lineage import utcnow
from src.workbench.journey_config import Settings
from src.workbench.operations_sdk import call,campaign,await_job,generate,write_report_file
from src.data.journey import extract,prepare,FEATURES
from src.data.storage import s3,bucket


def main():
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['serving','negative','mlflow-down']);args=parser.parse_args()
    if os.getenv('POC_PROJECT')!='marista-correcoes-isolated' or os.getenv('POC_ISOLATED_TESTS')!='1':
        raise RuntimeError('Only the marked isolated project is allowed')
    cfg=Settings.load();mlflow.set_tracking_uri(cfg.tracking)
    headers={'Authorization':'Bearer '+required('INFERENCE_TOKEN')}
    proof={'test_id':args.stage,'executed_at_utc':utcnow(),'source_type':'DEMO','checks':{}}
    if args.stage=='mlflow-down':
        from src.workbench.journey_steps import dependencies,require_dependencies
        checks=dependencies(cfg,str(uuid4()))
        try:
            require_dependencies(checks,cfg)
        except RuntimeError:
            proof['checks']['preflight_blocks_before_fit']=True
        else:
            raise AssertionError('MLflow down did not block training')
        proof['dependencies']=checks
    elif args.stage=='serving':
        scenario=json.loads(Path('/reports/v3/scenario-latest.json').read_text())
        before=httpx.get(cfg.inference+'/internal/draft/cache',headers=headers,timeout=15).json()
        assert before['cache']['currsize']==0
        job=generate(cfg,scenario['generation_body'],'v3-restart-'+uuid4().hex)
        done=await_job(cfg,job['status_url']);assert done['status']=='COMPLETED',done
        audit=call(cfg,'GET',f"/v1/audit/proposal/{done['proposal_id']}")
        assert audit['status']=='VERIFIED',audit
        after=httpx.get(cfg.inference+'/internal/draft/cache',headers=headers,timeout=15).json()
        assert after['cache']['currsize']==3 and after['cache']['misses']==3
        proof.update(before=before,after=after,proposal_id=done['proposal_id'],audit=audit)
        proof['checks']['three_models_restored_without_jupyter']=True
    else:
        client=mlflow.MlflowClient();frame,snapshot=extract(cfg);_,_,future=prepare(frame,snapshot)
        name='hi.demo.v3-negative.'+uuid4().hex[:8]
        created=campaign(cfg,dict(snapshot_id=snapshot['id'],cycle_code=cfg.cycle,model_keys=[name],requested_by='isolated-v3',confirm_training=True),uuid4().hex)
        assert await_job(cfg,f"/v1/training/campaigns/{created['campaign_id']}")['status']=='COMPLETED'
        item=call(cfg,'GET',f"/v1/training/campaigns/{created['campaign_id']}/items")[0]
        result=item['result'];version=client.get_model_version(name,item['model_version'])
        body=dict(execution_id=version.tags['execution_id'],model_name=name,model_version=str(version.version),run_id=version.run_id,
            snapshot_id=snapshot['id'],records=future[FEATURES].head(1).to_dict('records'))
        def predict(payload):
            return httpx.post(cfg.inference+'/internal/draft/predict',headers=headers,json=payload,timeout=60)
        object_key=next(f['key'] for f in result['storage_evidence'] if f['key'].endswith('/model.pkl'))
        storage=s3()
        mutated=storage.put_object(Bucket=bucket(),Key=object_key,Body=b'isolated V3 checksum negative')
        try:
            assert predict(body).status_code==409
            assert call(cfg,'GET',f'/v1/audit/model?model_key={name}&version={version.version}')['status']=='MISMATCH'
            proof['checks']['corrupted_object_rejected']=True
        finally:
            storage.delete_object(Bucket=bucket(),Key=object_key,VersionId=mutated['VersionId'])
        marker=storage.delete_object(Bucket=bucket(),Key=object_key)
        try:
            assert predict(body).status_code==503
            proof['checks']['missing_object_rejected']=True
        finally:
            storage.delete_object(Bucket=bucket(),Key=object_key,VersionId=marker['VersionId'])
        import yaml
        metadata_key=next(f['key'] for f in result['storage_evidence'] if f['key'].endswith('/MLmodel'))
        response=storage.get_object(Bucket=bucket(),Key=metadata_key)
        try:
            metadata=yaml.safe_load(response['Body'].read())
        finally:
            response['Body'].close()
        metadata['signature']['outputs']=json.dumps([{'type':'string','required':True}])
        changed=storage.put_object(Bucket=bucket(),Key=metadata_key,Body=yaml.safe_dump(metadata).encode())
        try:
            assert predict(body).status_code==409
            proof['checks']['altered_model_signature_rejected_before_deserialization']=True
        finally:
            storage.delete_object(Bucket=bucket(),Key=metadata_key,VersionId=changed['VersionId'])
        assert predict(body).status_code==200
        client.set_model_version_tag(name,version.version,'snapshot_id',str(uuid4()))
        try:
            assert predict(body).status_code==409  # cached model must still check tags
            proof['checks']['conflicting_tag_rejected_with_warm_cache']=True
        finally:
            client.set_model_version_tag(name,version.version,'snapshot_id',snapshot['id'])
        # Deleting the same optional shared tag from both objects must not erase catalog evidence.
        original=version.tags['query_version']
        client.delete_model_version_tag(name,version.version,'query_version')
        client.delete_tag(version.run_id,'query_version')
        try:
            assert call(cfg,'GET',f'/v1/audit/model?model_key={name}&version={version.version}')['status']=='MISMATCH'
            proof['checks']['catalog_detects_shared_tag_deleted_from_both_objects']=True
        finally:
            client.set_model_version_tag(name,version.version,'query_version',original)
            client.set_tag(version.run_id,'query_version',original)
        assert predict(dict(body,snapshot_id=str(uuid4()))).status_code==409
        assert predict(dict(body,model_version='999999')).status_code!=200
        assert httpx.get(cfg.api+'/v1/audit/inventory',timeout=15).status_code==401
        def review(action):
            request=call(cfg,'POST','/v1/governance/requests',dict(model_name=name,model_version=str(version.version),action=action,reason='Explicit isolated V3 acceptance',requested_by='isolated-v3'))
            return call(cfg,'POST',f"/v1/governance/requests/{request['approval_id']}/review",dict(approve=True,confirm='REVIEW_EXPLICIT_VERSION'),operator=True)
        review('APPROVE')
        try:
            payload=dict(mode='APPROVED',cycle_code=cfg.cycle,snapshot_id=snapshot['id'],model_selectors=[dict(model_name=name,model_version=str(version.version))],requested_by='isolated-v3',confirm_demo=True)
            job=generate(cfg,payload,uuid4().hex);assert await_job(cfg,job['status_url'])['status']=='COMPLETED'
        finally:
            review('REVOKE')
        response=httpx.post(cfg.api+'/v1/proposals/generations',headers={'Authorization':'Bearer '+required('API_TOKEN'),'Idempotency-Key':uuid4().hex},json=payload,timeout=30)
        assert response.status_code==403
        proposal_key=f"lineage/poc/planilha-turmas/proposals/{job['job_id']}/revisions/1/manifest.json"
        altered=storage.put_object(Bucket=bucket(),Key=proposal_key,Body=b'{}')
        try:
            assert call(cfg,'GET',f"/v1/audit/proposal/{job['job_id']}")['status']=='MISMATCH'
            proof['checks']['altered_proposal_manifest_rejected']=True
        finally:
            storage.delete_object(Bucket=bucket(),Key=proposal_key,VersionId=altered['VersionId'])
        proof['checks'].update(revocation_blocks_warm_cache=True,wrong_snapshot_rejected=True,missing_version_rejected=True,no_auth_rejected=True)
        assert call(cfg,'GET',f'/v1/audit/model?model_key={name}&version={version.version}')['status']=='VERIFIED'
        proof.update(model_key=name,model_version=version.version,run_id=version.run_id)
    proof['status']='AUTO_PASS'
    path=Path('/reports/v3')/(args.stage+'.json');path.parent.mkdir(exist_ok=True,parents=True)
    write_report_file(path,json.dumps(proof,default=str,indent=2));print(json.dumps(proof['checks']))


if __name__=='__main__':
    main()
