"""Operational inference and immutable academic proposal. No fit in this path."""
import copy
import math
import json
from datetime import datetime, timezone
import httpx
from sqlalchemy import text
from src.persistence.db import engine, rows
from src.workbench.academic_data import load, prepare, FEATURES, TARGETS
from src.serving.academic import eligible
from src.operations.jobs import checkpoint, get
from src.common.settings import required
from src.common.lineage import put_manifest, sha256

RULE = 'academic-composition/1.0-reference-only'


def compose(manifest, predictions, proposal_id, correlation_id, revision):
    offers = copy.deepcopy(manifest['offers'])
    regular_by_cohort = {}
    for offer in offers:
        prediction = predictions.get(offer['offer_id'])
        activities = offer['activities']
        theory = [a['reference_planned_students'] for a in activities if a['kind'] == 'THEORY'
                  and a['reference_planned_students'] is not None]
        reference = max(theory) if theory else None
        components = {t: dict(value=None, raw_prediction=None, data_class='NOT_AVAILABLE', source_ref=None) for t in TARGETS}
        usages = []
        if prediction:
            cohort = prediction['cohort_id']
            values = prediction['values']
            if not all(math.isfinite(v) for v in values):
                raise ValueError('Nonfinite predictions')
            regular = max(0, math.ceil(values[0]))
            if cohort in regular_by_cohort and regular_by_cohort[cohort] != regular:
                raise ValueError('Regular demand must be identical within the same cohort')
            regular_by_cohort[cohort] = regular
            for target, value in zip(TARGETS, values):
                components[target] = dict(value=max(0, math.ceil(value)), raw_prediction=value,
                    data_class='AI_ESTIMATE', source_ref=prediction['usage']['inference_id'])
            usages = [prediction['usage']]
            offer['academic'].update(cohort_id=cohort, cohort_ingress=prediction['cohort_ingress'],
                                     mapping_status='SYNTHETIC_ONLY')
            offer['status'] = 'DRAFT_PENDING_COORDINATOR'
        else:
            offer['academic']['cohort_id'] = None
        offer['demand'] = dict(**components,
            estimated_total=sum(components[t]['value'] for t in TARGETS) if prediction else None,
            uncertainty=None, reference_planned_students=reference,
            composition_rule='CEIL_NONNEGATIVE_DISJOINT_DEMO_CATEGORIES', categories_disjoint='DEMO_ASSUMPTION')
        # Without homologated activity capacities, no allocation is invented.
        for activity in activities:
            activity.update(proposed_groups=[], proposal_status='PENDING_OFFICIAL_CAPACITY')
        offer['lineage'] = dict(snapshot_id=manifest['snapshot_id'], dataset_sha256=manifest['dataset_sha256'],
            model_usages=usages, ruleset_version=RULE, cold_start_strategy=manifest['cold_start_strategy'],
            data_completeness=manifest['data_completeness'], history_window=manifest['history_window'],
            feedback_cycles_count=0, fallback_reason=manifest['fallback_reason'])
        offer['warnings'] = ['Planejamento 2024.2 não é ocupação observada.',
            'Estimativas treinadas em histórico sintético; capacidade oficial não fornecida.',
            'Unificação e modulação dependem de dados e validação acadêmica.']
    return dict(schema_version='poc-planilha-turmas-v2', contract_status='PROVISORIO_PENDENTE_HOMOLOGACAO',
        proposal_id=proposal_id, correlation_id=correlation_id, execution_id=proposal_id,
        snapshot_id=manifest['snapshot_id'], dataset_sha256=manifest['dataset_sha256'], cycle_code=manifest['target'],
        proposal_revision=revision, phase='REGULAR_MATRIX_DRAFT', source_type='SEMI_SYNTHETIC_POC',
        status='DRAFT_PENDING_COORDINATOR', generated_at=datetime.now(timezone.utc).isoformat(),
        offers=sorted(offers, key=lambda r:r['offer_id']))


def publish(proposal_id):
    record=rows('SELECT * FROM planning.ai_proposals_v2 WHERE proposal_id=:id', {'id':proposal_id})[0]
    offers=[r['payload'] for r in rows('SELECT payload FROM planning.ai_proposal_offers_v2 WHERE proposal_id=:id ORDER BY offer_id', {'id':proposal_id})]
    document=dict(record['header'],offers=offers)
    if sha256(document)!=record['payload_sha256']:
        raise ValueError('Persisted proposal checksum mismatch')
    evidence=put_manifest(f'lineage/poc/planilha-turmas/v4/proposals/{proposal_id}/manifest.json',document)
    with engine().begin() as con:
        con.execute(text('UPDATE planning.ai_proposals_v2 SET manifest_uri=:uri,manifest_sha256=:sha WHERE proposal_id=:id'),
                    dict(id=proposal_id,uri=evidence['uri'],sha=evidence['sha256']))
    return dict(proposal_id=proposal_id,manifest=evidence,proposal_url=f'/v2/proposals/{proposal_id}/application-view')


def execute(job):
    body=job['request'];job_id=str(job['job_id'])
    for selector in body['model_selectors']:
        eligible(selector['model_name'],selector['model_version'],body['snapshot_id'])
    if rows('SELECT 1 FROM planning.ai_proposals_v2 WHERE proposal_id=:id',{'id':job_id}):
        return publish(job_id)
    saved=get(job_id)['result']
    if 'academic_composition' in saved:
        document=saved['academic_composition']
    else:
        frame,manifest=load(body['snapshot_id'])
        if manifest['target']!=body['cycle_code']:
            raise ValueError('Snapshot target cycle mismatch')
        predictions={};courses=set()
        for selector in body['model_selectors']:
            deployment=eligible(selector['model_name'],selector['model_version'],body['snapshot_id'])
            metadata=deployment['metadata'];course=metadata['course_code']
            if course in courses:
                raise ValueError('Overlapping model course scopes')
            courses.add(course)
            _,_,future=prepare(frame,course)
            request=dict(**selector,snapshot_id=body['snapshot_id'],records=future[FEATURES].to_dict('records'),
                         correlation_id=job_id,proposal_id=job_id)
            from src.common.tracing import trace_headers
            response=httpx.post(required('INFERENCE_URI')+'/internal/academic/predict',json=request,timeout=120,
                headers={'Authorization':'Bearer '+required('INFERENCE_TOKEN'), **trace_headers()})
            response.raise_for_status();result=response.json()
            for field in ('model_name','model_version','run_id','artifact_sha256'):
                if result[field]!=metadata[field]:
                    raise ValueError('Inference model identity mismatch')
            if len(result['predictions'])!=len(future):
                raise ValueError('Incomplete inference response')
            usage={k:result[k] for k in ('model_name','model_version','run_id','artifact_sha256','inference_id')}
            usage.update(model_uri=metadata['model_uri'],experiment_id=metadata['experiment_id'],
                         artifact_uri=metadata['artifact_uri'],manifest=metadata['manifest'] if 'manifest' in metadata else None)
            for record,values in zip(future.to_dict('records'),result['predictions']):
                predictions[record['offer_id']]=dict(values=values,usage=usage,cohort_id=record['cohort_id'],cohort_ingress=record['cohort_ingress'])
        if courses!=set(frame.course_code):
            raise ValueError('Select exactly one explicitly deployed model for every course in snapshot')
        document=compose(manifest,predictions,job_id,job['correlation_id'],body['proposal_revision'])
        checkpoint(job_id,{'academic_composition':document})
    for selector in body['model_selectors']:
        eligible(selector['model_name'],selector['model_version'],body['snapshot_id'])
    with engine().begin() as con:
        header={k:v for k,v in document.items() if k!='offers'}
        con.execute(text('''INSERT INTO planning.ai_proposals_v2(proposal_id,snapshot_id,cycle_code,revision,status,header,payload_sha256)
            VALUES (:id,:snapshot,:cycle,:revision,:status,CAST(:header AS jsonb),:sha)'''),
            dict(id=job_id,snapshot=body['snapshot_id'],cycle=body['cycle_code'],revision=body['proposal_revision'],
                 status=document['status'],header=json.dumps(header),sha=sha256(document)))
        con.execute(text('INSERT INTO planning.ai_proposal_offers_v2(proposal_id,offer_id,payload) VALUES (:id,:offer,CAST(:payload AS jsonb))'),
            [dict(id=job_id,offer=o['offer_id'],payload=json.dumps(o)) for o in document['offers']])
    return publish(job_id)
