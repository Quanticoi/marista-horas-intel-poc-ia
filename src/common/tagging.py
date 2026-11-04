"""Additive HI-LINEAGE/1.1 presentation and shared identity checks."""
import re
import unicodedata
from datetime import datetime, timezone
from src.common.lineage import sha256

SCHEMA = 'HI-LINEAGE/1.1'
MODEL_PATTERN = r'^(planilha-turmas-demo|hi\.(?:demo|pt\.demanda)\.[A-Za-z0-9_.-]+)$'
SHARED = ('solution_id','environment','domain','source_type','cycle_code','academic_cycle_id',
    'campus_code','course_code','period_code','model_family','snapshot_id','snapshot_sha256',
    'dataset_sha256','dataset_schema_version','data_as_of_utc','query_version','training_campaign_id',
    'campaign_display_name','operation_job_id','training_execution_id','experiment_id','experiment_name',
    'run_id','run_name','algorithm','code_version','config_hash','feature_schema_hash','model_key',
    'model_display_name','registered_model_name','model_version','artifact_uri','artifact_sha256',
    'model_signature_hash','validation_status','correlation_id','trace_id')


def component(value):
    value = unicodedata.normalize('NFKC', str(value)).upper()
    # Reject lossy transliteration: no two different academic codes silently collapse.
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9-]{0,39}', value):
        raise ValueError('Academic code must be an unambiguous ASCII code of at most 40 characters')
    return value


def functional_key(campus, course, period):
    key = 'hi.pt.demanda.'+'.'.join(component(x) for x in (campus,course,period))
    if len(key)>160:
        raise ValueError('Model key exceeds 160 characters')
    return key


def experiment_name(cycle):
    if not re.fullmatch(r'[0-9]{4}-[12]', cycle):
        raise ValueError('Invalid academic cycle')
    return 'HI/POC/PlanilhaTurmas/Demanda/'+cycle


def run_name(context, algorithm, timestamp_ms, attempt, job_id):
    stamp=datetime.fromtimestamp(timestamp_ms/1000,timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    return f"{context['model_key']}__{algorithm}__{stamp}__a{attempt:02}__{job_id[:8]}"


def assert_shared(run, version):
    """Fail closed on 1.1; never upgrade historical evidence just by its presence."""
    rt, vt = run.data.tags, version.tags
    modern = rt.get('lineage_schema_version')==SCHEMA or vt.get('lineage_schema_version')==SCHEMA
    if not modern:
        return 'LEGACY_PARTIAL'
    if rt.get('lineage_schema_version')!=SCHEMA or vt.get('lineage_schema_version')!=SCHEMA:
        raise ValueError('MISMATCH: lineage schema')
    for key in SHARED:
        if rt.get(key)!=vt.get(key):
            raise ValueError('MISMATCH: shared tag '+key)
    required=('run_id','model_key','model_version','artifact_sha256','model_signature_hash','snapshot_id')
    if any(not vt.get(k) for k in required):
        raise ValueError('MISSING: required version identity')
    if (version.run_id!=run.info.run_id or vt['run_id']!=run.info.run_id
        or vt['model_key']!=version.name or vt['model_version']!=str(version.version)
        or vt.get('artifact_uri')!=version.source or run.info.status!='FINISHED'):
        raise ValueError('MISMATCH: native Registry identity or unfinished run')
    return 'VERIFIED'


def signature_hash(signature):
    if signature is None or signature.inputs is None or signature.outputs is None:
        raise ValueError('MISSING: model input/output signature')
    return sha256(signature.to_dict())
