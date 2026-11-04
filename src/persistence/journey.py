"""Atomic, append-only draft proposal persistence, idempotent by execution UUID."""
import hashlib
import json
import math
import uuid
from sqlalchemy import text
from src.data.journey import KEYS
from src.workbench.journey_config import sql_engine

RULE = "POC-whole-cohort-ceil-capacity-v1"


def compose(future, predictions, capacity=40):
    if not isinstance(capacity, int) or capacity <= 0 or len(future) != len(predictions):
        raise ValueError("Invalid capacity or prediction count")
    lines = []
    for row, value in zip(future.to_dict("records"), predictions):
        raw = float(value)
        if not math.isfinite(raw):
            raise ValueError("Non-finite forecast")
        proposed = max(0, math.ceil(raw))
        lines.append({**{k: row[k] for k in KEYS}, "forecast_raw":raw,
            "proposed_students":proposed, "proposed_groups":math.ceil(proposed/capacity), "human_adjustment":None})
    if not lines or len({tuple(r[k] for k in KEYS) for r in lines}) != len(lines):
        raise ValueError("Empty or duplicate proposal keys")
    return lines


def persist(cfg, execution_id, snapshot, trace, lines, capacity=40):
    uuid.UUID(execution_id)
    metadata = dict(execution_id=execution_id, correlation_id=execution_id,
        cycle_id=snapshot["cycle_id"], snapshot_id=snapshot["id"], course_scope=cfg.course,
        dataset_sha256=snapshot["dataset_sha256"], run_id=trace["run_id"],
        experiment_id=trace["experiment_id"], model_name=trace["model_name"],
        model_version=trace["model_version"], artifact_uri=trace["artifact_uri"],
        rule_version=RULE, capacity=capacity, mode=cfg.mode, row_count=len(lines))
    content = {"metadata":metadata, "lines":sorted(lines, key=lambda r:tuple(r[k] for k in KEYS))}
    provenance = {k:trace[k] for k in ("inference_id","artifact_sha256","model_usages") if k in trace}
    if provenance:
        content["provenance"] = provenance
    payload = json.dumps(content, sort_keys=True)
    metadata["payload_sha256"] = hashlib.sha256(payload.encode()).hexdigest()
    engine = sql_engine(cfg.application, cfg.timeout)
    try:
        with engine.begin() as con:
            con.execute(text("SELECT pg_advisory_xact_lock(hashtext(:id))"), {"id":execution_id})
            old = con.execute(text("SELECT * FROM planning.proposal_generations WHERE execution_id=:id"), {"id":execution_id}).mappings().first()
            if old:
                if old["payload_sha256"] != metadata["payload_sha256"]:
                    raise ValueError("Execution ID reused with different payload; create a new execution")
                return dict(old)
            columns = list(metadata)
            con.execute(text(f"INSERT INTO planning.proposal_generations ({','.join(columns)},status) VALUES ({','.join(':'+k for k in columns)},'DRAFT')"), metadata)
            con.execute(text("""INSERT INTO planning.proposal_lines
                (execution_id,course_id,period_id,discipline_id,forecast_raw,proposed_students,proposed_groups,human_adjustment)
                VALUES (:execution_id,:course_id,:period_id,:discipline_id,:forecast_raw,:proposed_students,:proposed_groups,:human_adjustment)"""),
                [dict(row, execution_id=execution_id) for row in lines])
            from src.persistence.db import audit
            from src.persistence.lineage import attach
            attach(con, execution_id, snapshot, trace, lines, RULE, capacity)
            audit(con, "jupyter-DEMO", "PROPOSAL_CREATED", "proposal", execution_id, execution_id,
                {"run_id":trace["run_id"], "rows":len(lines), "rule":RULE})
            return dict(con.execute(text("SELECT * FROM planning.proposal_generations WHERE execution_id=:id"), {"id":execution_id}).mappings().one())
    finally:
        engine.dispose()
