"""Approved V4 inference inside the existing inference service, bounded cache."""
from datetime import datetime,timezone
from uuid import UUID,uuid4
from threading import RLock
from collections import OrderedDict
import time
import pandas as pd
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,ConfigDict,Field
from src.serving.academic import eligible
from src.inference.journey import load_checked
from src.persistence.db import rows
from src.workbench.academic_data import FEATURES
from src.common.logging import event
from src.common.tracing import operation_span

resident=OrderedDict()
lock=RLock()
models=OrderedDict()
stats=dict(hits=0,misses=0,errors=0)


def load(name,version,snapshot_id=None):
    deployment=eligible(name,version,snapshot_id,role='readonly')
    metadata=deployment['metadata'];key=(name,version)
    started=time.monotonic()
    with lock:
        cache_key=(name,version,metadata['artifact_sha256'],metadata['signature_hash'])
        model=models.pop(cache_key,None)
        if model is None:
            stats['misses']+=1
            # Share verified loader implementation, not the legacy cache/index.
            with operation_span('model.load',model_name=name,model_version=version):
                model=load_checked.__wrapped__(*cache_key)
        else:
            stats['hits']+=1
        models[cache_key]=model
        prior=resident.pop(key,{})
        resident[key]=dict(model_name=name,model_version=version,loaded_at_utc=prior.get('loaded_at_utc',datetime.now(timezone.utc).isoformat()),
            last_used_at=datetime.now(timezone.utc).isoformat(),load_seconds=time.monotonic()-started,
            hits=prior.get('hits',0)+(1 if prior else 0),misses=prior.get('misses',0)+(0 if prior else 1))
        while len(models)>4:
            expired,_=models.popitem(last=False)
            resident.pop(expired[:2],None)
    return model,metadata


def preload():
    for record in rows("SELECT model_name,model_version FROM planning.academic_deployments WHERE policy='PRELOAD' AND status='DEPLOYED' AND expires_at>now()",role='readonly'):
        try:
            load(record['model_name'],record['model_version'])
        except Exception as error:
            event('inference','V4 preload refused',level='ERROR',model_key=record['model_name'],error_type=type(error).__name__)


class Predict(BaseModel):
    model_config=ConfigDict(extra='forbid')
    model_name:str=Field(pattern=r'^hi\.demo\.v4\.c[0-9]+\.components$')
    model_version:str=Field(pattern=r'^[1-9][0-9]*$')
    snapshot_id:UUID
    records:list[dict]=Field(min_length=1,max_length=500)
    correlation_id:UUID
    proposal_id:UUID|None=None


def router(auth):
    routes=APIRouter()
    @routes.get('/internal/academic/runtime',dependencies=[Depends(auth)])
    def runtime():
        with lock:
            result=list(resident.values())
        return dict(versions=result,cache=dict(stats,currsize=len(models),maxsize=4))
    @routes.post('/internal/academic/predict',dependencies=[Depends(auth)])
    def predict(body:Predict):
        try:
            model,metadata=load(body.model_name,body.model_version,body.snapshot_id)
            frame=pd.DataFrame(body.records)
            if set(frame.columns)!=set(FEATURES):
                raise ValueError('Unexpected input signature')
            frame=frame[FEATURES].astype(float)
            import numpy as np
            if not np.isfinite(frame.to_numpy()).all():
                raise ValueError('Nonfinite input')
            with operation_span('model.predict',model_name=body.model_name,model_version=body.model_version,rows=len(frame)):
                prediction=model.predict(frame)
            if prediction.shape!=(len(frame),3) or not np.isfinite(prediction).all():
                raise ValueError('Invalid model output')
            inference_id=str(uuid4())
            from src.common.lineage import put_manifest,sha256,utcnow
            put_manifest(f'lineage/poc/planilha-turmas/v4/inferences/{inference_id}/manifest.json',
                dict(schema_version='HI-LINEAGE/1.2',inference_id=inference_id,created_at=utcnow(),
                     correlation_id=str(body.correlation_id),proposal_id=str(body.proposal_id) if body.proposal_id else None,
                     model_name=body.model_name,model_version=body.model_version,run_id=metadata['run_id'],
                     snapshot_id=str(body.snapshot_id),artifact_sha256=metadata['artifact_sha256'],
                     input_sha256=sha256(body.records),prediction_sha256=sha256(prediction.tolist()),row_count=len(frame)))
            event('inference','academic prediction',correlation_id=str(body.correlation_id),inference_id=inference_id,
                  model_key=body.model_name,model_version=body.model_version,run_id=metadata['run_id'],rows=len(frame))
            return dict(inference_id=inference_id,model_name=body.model_name,model_version=body.model_version,
                run_id=metadata['run_id'],artifact_sha256=metadata['artifact_sha256'],snapshot_id=str(body.snapshot_id),
                proposal_id=str(body.proposal_id) if body.proposal_id else None,predictions=prediction.tolist())
        except PermissionError:
            raise HTTPException(403,'Explicit approved deployment required') from None
        except ValueError:
            raise HTTPException(422,'Incompatible academic request or model metadata') from None
        except Exception as error:
            stats['errors']+=1
            event('inference','academic dependency failure',level='ERROR',error_type=type(error).__name__)
            raise HTTPException(503,'Academic model dependencies unavailable') from None
    return routes
