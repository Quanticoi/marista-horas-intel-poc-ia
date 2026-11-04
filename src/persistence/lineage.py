"""Transactional lineage adapter; never mutates the original proposal."""
import json
from sqlalchemy import text
from src.common.lineage import CONTRACT, canonical, sha256, manifest, put_manifest


def entity(con, kind, external_id, attributes):
    con.execute(text("""INSERT INTO planning.lineage_entities
        (entity_type,external_id,environment,domain,attributes)
        VALUES (:kind,:external,'poc','planilha-turmas',CAST(:attributes AS jsonb))
        ON CONFLICT(entity_type,environment,external_id) DO NOTHING"""),
        dict(kind=kind,external=str(external_id),attributes=canonical(attributes).decode()))
    row = con.execute(text("""SELECT entity_id,attributes FROM planning.lineage_entities
        WHERE entity_type=:kind AND external_id=:external AND environment='poc'"""),
        dict(kind=kind,external=str(external_id))).mappings().one()
    if canonical(row["attributes"]) != canonical(attributes):
        raise ValueError("Immutable lineage identity collision")
    return row["entity_id"]


def edge(con, parent, child, relation):
    con.execute(text("""INSERT INTO planning.lineage_edges(parent_id,child_id,relation_type)
        VALUES (:parent,:child,:relation) ON CONFLICT DO NOTHING"""),
        dict(parent=parent,child=child,relation=relation))


def attach(con, execution_id, snapshot, trace, lines, rule, capacity):
    usages = trace.get("model_usages") or [dict(model_key=trace["model_name"],
        registered_model_name=trace["model_name"],model_version=trace["model_version"],
        run_id=trace["run_id"],snapshot_id=snapshot["id"],artifact_uri=trace["artifact_uri"],
        artifact_sha256=trace.get("artifact_sha256"),inference_id=trace.get("inference_id"),
        line_keys=["/".join(str(r[k]) for k in ("course_id","period_id","discipline_id")) for r in lines])]
    proposal = entity(con,"proposal",execution_id,{"proposal_revision":1})
    for usage in usages:
        data = dict(usage,proposal_id=execution_id,ruleset_hash=sha256({"version":rule,"capacity":capacity}),
            provenance_status="VERIFIED" if usage.get("artifact_sha256") and usage.get("inference_id") else "LEGACY_PARTIAL")
        keys = ("proposal_id","inference_id","model_key","registered_model_name","model_version","run_id",
                "snapshot_id","artifact_uri","artifact_sha256","ruleset_hash","line_keys","provenance_status")
        data = {k:data.get(k) for k in keys}
        data["line_keys"] = json.dumps(data["line_keys"])
        con.execute(text("INSERT INTO planning.proposal_model_usage ("+",".join(keys)+") VALUES ("+
            ",".join("CAST(:line_keys AS jsonb)" if k=="line_keys" else ":"+k for k in keys)+")"),data)
        snap = entity(con,"snapshot",usage["snapshot_id"],{})
        run = entity(con,"run",usage["run_id"],{})
        model = entity(con,"model",usage["registered_model_name"]+"/"+usage["model_version"],
                       {"model_key":usage["model_key"],"run_id":usage["run_id"]})
        edge(con,snap,run,"TRAINED_ON")
        edge(con,run,model,"REGISTERED_AS")
        edge(con,model,proposal,"CONTRIBUTED_TO")
        if usage.get("inference_id"):
            inference = entity(con,"inference",usage["inference_id"],{})
            edge(con,model,inference,"PREDICTED_WITH")
            edge(con,inference,proposal,"CONTRIBUTED_TO")
    from src.api.proposal_contract import build_view
    # Full representation evidence has an explicit limit matching persisted row_count.
    view = build_view(con,execution_id,len(lines),0)
    con.execute(text("""INSERT INTO planning.proposal_contract_evidence
        (proposal_id,proposal_revision,schema_version,payload_sha256,published_at_utc,row_count,validation_status)
        VALUES (:id,1,:schema,:hash,:generated,:count,'DEMO_PARTIAL')"""),
        dict(id=execution_id,schema=CONTRACT,hash=view.payload_sha256,generated=view.generated_at_utc,count=len(lines)))


def publish_manifest(cfg, execution_id):
    from src.workbench.journey_config import sql_engine
    from src.api.proposal_contract import build_view
    engine = sql_engine(cfg.application,cfg.timeout)
    try:
        with engine.connect() as con:
            count = con.execute(text("SELECT row_count FROM planning.proposal_generations WHERE execution_id=:id"),{"id":execution_id}).scalar_one()
            view = build_view(con,execution_id,count,0)
    finally:
        engine.dispose()
    doc = manifest("proposal",{},view.generated_at_utc.isoformat(),
                   proposal_id=str(view.proposal_id),proposal_revision=1,schema_version=CONTRACT,
                   payload_sha256=view.payload_sha256,lineage=view.lineage)
    return put_manifest(f"lineage/poc/planilha-turmas/proposals/{execution_id}/revisions/1/manifest.json",doc)
