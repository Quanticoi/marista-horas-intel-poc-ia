"""Evidence-based cross-store verification, distinct from mere catalog recording."""
import json
from src.api.academic import application_view
from src.persistence.db import rows
from src.common.lineage import sha256
from src.data.storage import s3,bucket
from src.serving.academic import validate
from src.workbench.academic_data import load


def object_json(key):
    response=s3().get_object(Bucket=bucket(),Key=key)
    try:
        raw=response['Body'].read()
    finally:
        response['Body'].close()
    return json.loads(raw),sha256(raw)


def proposal(proposal_id):
    payload=application_view(proposal_id,limit=500)
    record=rows('SELECT * FROM planning.ai_proposals_v2 WHERE proposal_id=:id',{'id':proposal_id})[0]
    document,digest=object_json(f'lineage/poc/planilha-turmas/v4/proposals/{proposal_id}/manifest.json')
    expected={k:v for k,v in payload.items() if k not in ('total_rows','limit','offset','filters','payload_sha256','proposal_sha256')}
    if document!=expected or digest!=record['manifest_sha256'] or digest!=record['payload_sha256']:
        raise ValueError('SQL/HTTP/object-store proposal mismatch')
    _,snapshot=load(payload['snapshot_id'])
    if snapshot['dataset_sha256']!=payload['dataset_sha256']:
        raise ValueError('Proposal snapshot mismatch')
    sources={str(r['source_row_id']):r['payload'] for r in rows('SELECT source_row_id,payload FROM planning.academic_reference_rows')}
    observed=[a['source_row_id'] for o in payload['offers'] for a in o['activities']]
    if len(observed)!=len(set(observed)) or set(observed)!={str(k) for k in sources}:
        raise ValueError('Reference activity lineage missing or duplicated')
    for offer in payload['offers']:
        for activity in offer['activities']:
            original=sources[activity['source_row_id']]
            for target,source in [('source_file_sha256','source_file_sha256'),('source_row_number','source_row_number'),
                ('source_sheet','source_sheet'),('reference_planned_students','planned_students'),('reference_seats','offered_seats')]:
                if activity[target]!=original[source]:
                    raise ValueError('Proposal activity differs from immutable source')
    models={};inferences={}
    for offer in payload['offers']:
        for usage in offer['lineage']['model_usages']:
            key=usage['model_name']+'/'+usage['model_version']
            if key not in models:
                result=validate(usage['model_name'],usage['model_version'])
                if any(result[k]!=usage[k] for k in ('run_id','artifact_sha256')):
                    raise ValueError('Proposal/model mismatch')
                models[key]=dict(model_name=usage['model_name'],model_version=usage['model_version'],
                                run_id=usage['run_id'],status='VERIFIED',artifact_sha256=usage['artifact_sha256'])
            iid=usage['inference_id']
            if iid not in inferences:
                evidence,_=object_json(f'lineage/poc/planilha-turmas/v4/inferences/{iid}/manifest.json')
                if any(evidence[k]!=usage[k] for k in ('model_name','model_version','run_id','artifact_sha256')) or evidence['proposal_id']!=proposal_id:
                    raise ValueError('Inference lineage mismatch')
                attributed=sorted([o for o in payload['offers'] if any(u['inference_id']==iid for u in o['lineage']['model_usages'])],key=lambda o:o['offer_id'])
                predicted=[[o['demand'][t]['raw_prediction'] for t in ('regular','dependency','elective')] for o in attributed]
                if sha256(predicted)!=evidence['prediction_sha256'] or len(predicted)!=evidence['row_count']:
                    raise ValueError('Persisted offer predictions differ from inference evidence')
                inferences[iid]=dict(inference_id=iid,status='VERIFIED')
    return dict(proposal_id=proposal_id,status='VERIFIED',proposal_sha256=digest,offers=len(payload['offers']),
                source_rows=len(observed),models=list(models.values()),inferences=list(inferences.values()),
                limitations=['Technical integrity only; no academic approval or real forecast quality asserted.'])
