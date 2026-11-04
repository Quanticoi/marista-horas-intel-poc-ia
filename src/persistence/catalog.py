"""Academic presentation catalog; all writes are additive in the application DB."""
import json
from datetime import datetime, timezone
from sqlalchemy import text
from src.common.lineage import canonical, put_manifest
from src.common.tagging import SCHEMA, functional_key, assert_shared, signature_hash
from src.persistence.db import rows, engine


def scopes():
    values=rows('''SELECT m.id::text AS catalog_id,c.id::text AS campus_id,
        cr.id::text AS course_id,p.id::text AS period_id,c.code AS campus_code,
        cr.code AS course_code,p.period_number FROM planning.model_catalog m
        JOIN planning.campuses c ON c.id=m.campus_id JOIN planning.courses cr ON cr.id=m.course_id
        JOIN planning.academic_periods p ON p.id=m.period_id WHERE m.active
        AND EXISTS(SELECT 1 FROM planning.historical_enrollments h JOIN planning.dataset_snapshots s ON s.id=h.snapshot_id
                   WHERE h.period_id=p.id AND s.source_reference='SYNTHETIC')
        ORDER BY c.code,cr.code,p.period_number''')
    seen={}
    for item in values:
        item.update(campus_code='DEMO-'+item['campus_code'],course_code='DEMO-'+item['course_code'],
                    period_code='P'+str(item['period_number']),model_family='demanda-alunos')
        item['model_key']=functional_key(item['campus_code'],item['course_code'],item['period_code'])
        if item['model_key'] in seen and seen[item['model_key']]!=item['catalog_id']:
            raise ValueError('Academic naming collision')
        seen[item['model_key']]=item['catalog_id']
        item['model_display_name']=f"Planilha Turmas DEMO • {item['campus_code']} • {item['course_code']} • Período {item['period_number']}"
    return values


def context_for(name):
    if name.startswith('hi.pt.demanda.'):
        matches=[x for x in scopes() if x['model_key']==name]
        if len(matches)!=1:
            raise ValueError('Functional model key does not match a unique seeded academic scope')
        return matches[0]
    return dict(model_key=name,model_display_name='Ensaio DEMO agregado • '+name,model_family='demanda-alunos')


def publish(client, version, files):
    """Recoverable immutable checkpoint, timestamp comes from native Registry version."""
    import mlflow
    run=client.get_run(version.run_id)
    if assert_shared(run,version)!='VERIFIED':
        return None
    tags=version.tags
    info=mlflow.models.get_model_info(f'models:/{version.name}/{version.version}')
    if signature_hash(info.signature)!=tags['model_signature_hash']:
        raise ValueError('MISMATCH: model signature')
    binary=next(f for f in files if f['key'].endswith('/model.pkl'))
    if binary['sha256']!=tags['artifact_sha256']:
        raise ValueError('MISMATCH: model bytes and Registry tag')
    key=f"lineage/poc/planilha-turmas/catalog/cycles/{tags['cycle_code']}/models/{version.name}/versions/v{int(version.version):04}/manifest.json"
    document=dict(tags,manifest_schema_version=SCHEMA,model_version=int(version.version),
        created_at_utc=datetime.fromtimestamp(version.creation_timestamp/1000,timezone.utc).isoformat(),
        status_at_creation='DEMO_CANDIDATE',files=files,
        sql_reference='planejamento_db.planning.model_version_catalog')
    reference=put_manifest(key,document)
    value=dict(model_key=version.name,version=str(version.version),run_id=version.run_id,
        snapshot=tags['snapshot_id'],campaign=tags.get('training_campaign_id'),
        document=json.dumps(document,ensure_ascii=False),uri=reference['uri'],hash=reference['sha256'])
    with engine().begin() as con:
        con.execute(text('''INSERT INTO planning.model_version_catalog
            (model_key,model_version,run_id,snapshot_id,campaign_id,metadata,manifest_uri,manifest_sha256)
            VALUES (:model_key,:version,:run_id,:snapshot,:campaign,CAST(:document AS jsonb),:uri,:hash)
            ON CONFLICT (model_key,model_version) DO NOTHING'''),value)
        old=con.execute(text('SELECT metadata,manifest_uri,manifest_sha256 FROM planning.model_version_catalog WHERE model_key=:model_key AND model_version=:version'),value).mappings().one()
        if canonical(old['metadata'])!=canonical(document) or old['manifest_uri']!=reference['uri'] or old['manifest_sha256']!=reference['sha256']:
            raise ValueError('MISMATCH: immutable SQL catalog collision')
    return dict(manifest_uri=reference['uri'],manifest_sha256=reference['sha256'],**tags)


def inventory(model_key=None,run_id=None,snapshot_id=None,campaign_id=None,limit=100,offset=0):
    if not 1<=limit<=500 or offset<0:
        raise ValueError('Invalid inventory page')
    return rows('''SELECT * FROM planning.v_model_inventory WHERE
        (CAST(:model AS text) IS NULL OR model_key=:model) AND (CAST(:run AS text) IS NULL OR run_id=:run)
        AND (CAST(:snapshot AS uuid) IS NULL OR snapshot_id=:snapshot)
        AND (CAST(:campaign AS uuid) IS NULL OR campaign_id=:campaign)
        ORDER BY model_key,model_version::integer DESC LIMIT :limit OFFSET :offset''',
        dict(model=model_key,run=run_id,snapshot=snapshot_id,campaign=campaign_id,limit=limit,offset=offset))


def publish_campaign(campaign_id):
    campaign=rows('SELECT * FROM planning.training_campaigns WHERE campaign_id=:id',{'id':campaign_id})[0]
    members=rows('SELECT model_key,model_version,run_id,manifest_uri,manifest_sha256 FROM planning.model_version_catalog WHERE campaign_id=:id ORDER BY model_key,model_version::integer',{'id':campaign_id})
    if campaign['status']!='COMPLETED' or len(members)!=campaign['requested_count']:
        return None  # Historical/incomplete campaigns are not fabricated into full catalogs.
    return put_manifest(f'lineage/poc/planilha-turmas/catalog/campaigns/{campaign_id}/manifest.json',dict(
        manifest_schema_version=SCHEMA,source_type='DEMO',environment='poc',training_campaign_id=str(campaign_id),
        campaign_display_name=campaign['request'].get('campaign_display_name','Campanha DEMO'),
        cycle_code=campaign['request']['cycle_code'],snapshot_id=campaign['request']['snapshot_id'],
        created_at_utc=campaign['created_at_utc'].isoformat(),status_at_creation='COMPLETED',models=members))
