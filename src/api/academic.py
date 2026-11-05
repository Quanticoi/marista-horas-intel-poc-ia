"""V4 reads and explicit operational commands; scientific execution stays in Workbench."""
from uuid import UUID
from typing import Literal
import httpx
from fastapi import APIRouter,Depends,Header,HTTPException,Query,Request
from src.api.operations import operator,result
from src.api.academic_contract import Generation,ApplicationView,Selector
from src.persistence.db import rows
from src.operations import jobs
from src.common.settings import required
from src.common.lineage import sha256


def application_view(proposal_id, filters=None, limit=100, offset=0):
    records=rows('''SELECT p.* FROM planning.ai_proposals_v2 p JOIN planning.operation_jobs j ON j.job_id=p.proposal_id
        WHERE p.proposal_id=:id AND p.manifest_uri IS NOT NULL AND j.status='COMPLETED' ''',{'id':proposal_id})
    if not records:
        raise LookupError('Completed published academic proposal not found')
    record=records[0];filters=filters or {}
    offers=[r['payload'] for r in rows('SELECT payload FROM planning.ai_proposal_offers_v2 WHERE proposal_id=:id ORDER BY offer_id',{'id':proposal_id})]
    if sha256(dict(record['header'],offers=offers))!=record['payload_sha256']:
        raise ValueError('Persisted proposal checksum mismatch')
    def matches(offer):
        for key,value in filters.items():
            actual=record['cycle_code'] if key=='cycle_code' else offer['status'] if key=='status' else offer['academic'].get(key)
            if str(actual)!=str(value):
                return False
        return True
    selected=[o for o in offers if matches(o)]
    payload=dict(record['header'],offers=selected[offset:offset+limit],total_rows=len(selected),limit=limit,offset=offset,
                 filters=filters,proposal_sha256=record['payload_sha256'])
    payload['payload_sha256']=sha256(payload)
    ApplicationView.model_validate(payload)
    return payload


class Deploy(Selector):
    policy:Literal['LAZY','PRELOAD']


def router(auth):
    routes=APIRouter()

    @routes.get('/v1/academic/scopes',dependencies=[Depends(auth)])
    def scopes():
        return dict(snapshots=rows('SELECT snapshot_id,manifest->>\'target\' AS cycle_code,manifest->>\'scenario_id\' AS scenario_id FROM planning.academic_simulation_snapshots ORDER BY snapshot_id'),
                    courses=rows('SELECT * FROM planning.academic_course_identity ORDER BY course_code,shift'),
                    curricula=rows('SELECT * FROM planning.curriculum_identity ORDER BY course_id,curriculum_code'),
                    cohorts=rows('SELECT * FROM planning.academic_cohort ORDER BY snapshot_id,cohort_id'))

    @routes.get('/v1/academic/data-quality',dependencies=[Depends(auth)])
    def quality():
        return rows('SELECT payload->>\'status\' AS status,count(*) AS rows FROM planning.academic_reference_rows GROUP BY payload->>\'status\' ORDER BY status')

    @routes.get('/v1/workbench/metric-catalog',dependencies=[Depends(auth)])
    def metrics():
        from src.workbench.metrics_v4 import catalog
        return catalog()

    @routes.get('/v1/serving/models',dependencies=[Depends(auth)])
    def catalog():
        return rows('''SELECT w.model_key,w.result->>'model_version' AS model_version,w.result->>'course_code' AS course_code,
          w.result->>'validation_status' AS validation_status,w.run_id,w.result->>'snapshot_id' AS snapshot_id,
          a.status AS approval_status,d.status AS deployment_status,d.policy,d.expires_at
          FROM planning.workbench_models w LEFT JOIN planning.model_approval_requests a
          ON a.model_name=w.model_key AND a.model_version=w.result->>'model_version' AND a.status='APPROVED'
          LEFT JOIN planning.academic_deployments d ON d.model_name=w.model_key AND d.model_version=w.result->>'model_version'
          WHERE w.state='COMPLETED' ORDER BY w.model_key,(w.result->>'model_version')::integer''')

    @routes.post('/v1/serving/models/{model_key}/deploy')
    def deploy(model_key:str,body:Deploy,idempotency_key:str=Header(min_length=1,max_length=160),actor=Depends(operator)):
        if model_key!=body.model_name:
            raise HTTPException(422,'Model path/body mismatch')
        from src.serving.academic import deploy
        try:
            return deploy(model_key,body.model_version,body.policy,idempotency_key,actor)
        except PermissionError:
            raise HTTPException(403,'Explicit technical approval required') from None

    @routes.get('/v1/serving/runtime',dependencies=[Depends(auth)])
    def runtime():
        response=httpx.get(required('INFERENCE_URI')+'/internal/academic/runtime',timeout=15,
            headers={'Authorization':'Bearer '+required('INFERENCE_TOKEN')})
        response.raise_for_status()
        return response.json()

    @routes.post('/v2/proposals/generations',status_code=202,dependencies=[Depends(auth)])
    def generate(body:Generation,request:Request,idempotency_key:str=Header(min_length=1,max_length=160)):
        payload=body.model_dump(mode='json')
        prior=rows("SELECT * FROM planning.operation_jobs WHERE kind='generation' AND idempotency_key=:key",{'key':idempotency_key})
        if prior:
            if prior[0]['request_hash']!=sha256(payload):
                raise jobs.Conflict('Idempotency key reused with different payload')
            jobs.submit(prior[0]['job_id'])
            return result(prior[0])
        from src.workbench.academic_data import load
        from src.serving.academic import eligible
        frame,manifest=load(str(body.snapshot_id))
        if manifest['target']!=body.cycle_code:
            raise HTTPException(409,'Snapshot cycle mismatch')
        courses=[]
        try:
            for selector in body.model_selectors:
                deployment=eligible(selector.model_name,selector.model_version,body.snapshot_id)
                courses.append(deployment['metadata']['course_code'])
        except PermissionError:
            raise HTTPException(403,'Explicit approved deployment required') from None
        if len(set(courses))!=len(courses) or set(courses)!=set(frame.course_code):
            raise HTTPException(422,'Select one deployed model for each snapshot course')
        job=jobs.create('generation',payload,idempotency_key,body.requested_by,request.state.correlation_id)
        jobs.submit(job['job_id'])
        return result(job)

    @routes.get('/v2/proposals',dependencies=[Depends(auth)])
    def proposals(limit:int=Query(50,ge=1,le=500)):
        return rows('''SELECT p.proposal_id,p.cycle_code,p.revision,p.status,p.generated_at,p.snapshot_id
          FROM planning.ai_proposals_v2 p JOIN planning.operation_jobs j ON j.job_id=p.proposal_id
          WHERE p.manifest_uri IS NOT NULL AND j.status='COMPLETED' ORDER BY p.generated_at DESC,p.proposal_id LIMIT :limit''',{'limit':limit})

    @routes.get('/v2/proposals/{proposal_id}/application-view',response_model=ApplicationView,dependencies=[Depends(auth)])
    def view(proposal_id:UUID,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0),
        cycle_code:str|None=None,school:str|None=None,course_code:str|None=None,curriculum_code:str|None=None,
        cohort_id:UUID|None=None,period:int|None=None,shift:str|None=None,discipline_code:str|None=None,
        offer_type:str|None=None,status:str|None=None):
        filters={k:str(v) if isinstance(v,UUID) else v for k,v in locals().items() if k not in ('proposal_id','limit','offset') and v is not None}
        return application_view(proposal_id,filters,limit,offset)

    @routes.get('/v2/audit/proposals/{proposal_id}',dependencies=[Depends(auth)])
    def audit(proposal_id:UUID):
        from src.serving.audit import proposal
        return proposal(str(proposal_id))
    return routes
