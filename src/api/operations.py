import hmac
import os
from uuid import UUID
from typing import Literal
from fastapi import APIRouter,Depends,Header,HTTPException,Query,Request
from pydantic import Field
from src.operations.contracts import Generation,Campaign,Selector,Strict
from src.operations import jobs
from src.persistence.db import rows
from src.common.settings import required

def operator(authorization:str=Header(default="")):
    if not hmac.compare_digest(authorization,"Bearer "+required("OPERATOR_TOKEN")):
        raise HTTPException(403,"Authorized operator credential required")
    return os.getenv("OPERATOR_ID","poc-reviewer")

class ReviewRequest(Selector):
    action:Literal["APPROVE","REVOKE","ROLLBACK"]="APPROVE"
    requested_by:str=Field(min_length=1,max_length=120)
    reason:str=Field(min_length=8,max_length=1000)

class Decision(Strict):
    approve:bool
    confirm:Literal["REVIEW_EXPLICIT_VERSION"]

def result(job):
    return dict(generation_job_id=job["job_id"],job_id=job["job_id"],correlation_id=job["correlation_id"],
        status=job["status"],attempt=job["attempt"],error_code=job["error_code"],
        status_url=f"/v1/proposals/generations/{job['job_id']}",
        proposal_id=job["result"].get("proposal_id"),proposal_url=job["result"].get("proposal_url"),
        trace_id=job["result"].get("trace_id"),
        started_at_utc=job["started_at_utc"],ended_at_utc=job["ended_at_utc"])

def validate_snapshot(snapshot_id,cycle):
    if not rows("""SELECT s.id FROM planning.dataset_snapshots s JOIN planning.academic_cycles c ON c.id=s.cycle_id
        WHERE s.id=:snapshot AND c.cycle_code=:cycle AND s.sealed_at IS NOT NULL AND s.source_reference='SYNTHETIC'""",dict(snapshot=snapshot_id,cycle=cycle)):
        raise HTTPException(404,"Compatible sealed DEMO snapshot not found")

def router(auth):
    routes=APIRouter()

    @routes.post("/v1/proposals/generations",status_code=202,dependencies=[Depends(auth)])
    def generate(body:Generation,request:Request,idempotency_key:str=Header(min_length=1,max_length=160)):
        from src.common.lineage import sha256
        payload=body.model_dump(mode="json")
        existing=rows("SELECT * FROM planning.operation_jobs WHERE kind='generation' AND idempotency_key=:key",{"key":idempotency_key})
        if existing:
            if existing[0]["request_hash"]!=sha256(payload):
                raise jobs.Conflict("Idempotency key reused with different payload")
            jobs.submit(existing[0]["job_id"])
            return result(existing[0])
        validate_snapshot(body.snapshot_id,body.cycle_code)
        import mlflow
        from mlflow.exceptions import MlflowException
        for selected in body.model_selectors:
            try:
                version=mlflow.MlflowClient().get_model_version(selected.model_name,selected.model_version)
            except MlflowException as error:
                if error.error_code=="RESOURCE_DOES_NOT_EXIST":
                    raise HTTPException(404,"Model version not found") from None
                raise
            if version.tags.get("snapshot_id")!=str(body.snapshot_id):
                raise HTTPException(409,"Model snapshot mismatch")
        if body.mode=="APPROVED":
            from src.operations.generation import assert_approved
            try:
                for selected in body.model_selectors:
                    assert_approved(selected.model_name,selected.model_version)
            except Exception:
                raise HTTPException(403,"Selected version is not approved") from None
        job=jobs.create("generation",body.model_dump(mode="json"),idempotency_key,body.requested_by,request.state.correlation_id)
        jobs.submit(job["job_id"])
        return result(job)

    @routes.get("/v1/proposals/generations/{job_id}",dependencies=[Depends(auth)])
    def status(job_id:UUID):
        job=jobs.get(job_id)
        if job["kind"]!="generation":
            raise HTTPException(404,"Generation job not found")
        return dict(result(job),events=rows("SELECT event_type,details,created_at_utc FROM planning.operation_events WHERE job_id=:id ORDER BY event_id",{"id":job_id}))

    @routes.post("/v1/training/campaigns",status_code=202,dependencies=[Depends(auth)])
    def campaign(body:Campaign,request:Request,idempotency_key:str=Header(min_length=1,max_length=160)):
        validate_snapshot(body.snapshot_id,body.cycle_code)
        return jobs.create_campaign(body,idempotency_key,request.state.correlation_id)

    @routes.get("/v1/training/campaigns",dependencies=[Depends(auth)])
    def campaigns(limit:int=Query(50,ge=1,le=500),offset:int=Query(0,ge=0)):
        return rows("SELECT campaign_id,status,requested_count,created_at_utc,correlation_id FROM planning.training_campaigns ORDER BY created_at_utc DESC,campaign_id LIMIT :limit OFFSET :offset",dict(limit=limit,offset=offset))

    @routes.get("/v1/training/campaigns/{campaign_id}",dependencies=[Depends(auth)])
    def campaign_status(campaign_id:UUID):
        jobs.campaign_state(campaign_id)
        jobs.refresh_campaign(campaign_id)
        return jobs.campaign_state(campaign_id)

    @routes.get("/v1/training/campaigns/{campaign_id}/items",dependencies=[Depends(auth)])
    def items(campaign_id:UUID,limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
        jobs.campaign_state(campaign_id)
        return rows("SELECT * FROM planning.training_campaign_items WHERE campaign_id=:id ORDER BY model_key LIMIT :limit OFFSET :offset",dict(id=campaign_id,limit=limit,offset=offset))

    @routes.post("/v1/training/campaigns/{campaign_id}/{action}",dependencies=[Depends(auth)])
    def control(campaign_id:UUID,action:Literal["pause","resume","cancel","retry-failed"]):
        return jobs.control(campaign_id,action,"authenticated-poc-client")

    @routes.post("/v1/governance/requests",status_code=201,dependencies=[Depends(auth)])
    def approval_request(body:ReviewRequest,request:Request):
        from src.operations.governance import request_review
        return request_review(body.model_dump(),request.state.correlation_id)

    @routes.get("/v1/governance/requests",dependencies=[Depends(auth)])
    def approvals(limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
        return rows("SELECT * FROM planning.model_approval_requests ORDER BY created_at_utc DESC,approval_id LIMIT :limit OFFSET :offset",dict(limit=limit,offset=offset))

    @routes.get("/v1/governance/models",dependencies=[Depends(auth)])
    def registered_models(prefix:str=Query("",pattern=r"^[A-Za-z0-9_.-]{0,160}$"),limit:int=Query(100,ge=1,le=500),page_token:str=Query("",max_length=2048)):
        import mlflow
        models=mlflow.MlflowClient().search_registered_models(filter_string="name LIKE '"+prefix+"%'" if prefix else "",max_results=limit,page_token=page_token or None)
        return dict(items=[dict(model_name=m.name,aliases=m.aliases,tags=m.tags) for m in models],next_page_token=models.token)

    @routes.post("/v1/governance/requests/{approval_id}/review")
    def review(approval_id:UUID,body:Decision,actor=Depends(operator)):
        from src.operations.governance import review
        return review(approval_id,actor,body.approve)
    return routes
