import hashlib
import pandas as pd
from sqlalchemy import text
from src.common.settings import ROOT
from src.workbench.journey_config import sql_engine

QUERY = ROOT / "sql/queries/journey_history.sql"
KEYS = ["course_id", "period_id", "discipline_id"]
FEATURES = KEYS + ["semester_index", "semester"]
TARGET = "students"


def extract(cfg):
    engine = sql_engine(cfg.source, cfg.timeout)
    try:
        with engine.connect() as con:
            # Explicit DEMO source. Never select an arbitrary newest real dataset.
            snapshots = con.execute(text("""SELECT s.id::text, s.sha256 AS snapshot_sha256, c.id::text AS cycle_id,
                c.target_year*2+c.target_semester-1 AS target_index, c.target_semester
                FROM planning.dataset_snapshots s JOIN planning.academic_cycles c ON c.id=s.cycle_id
                WHERE c.cycle_code=:cycle AND s.source_reference='SYNTHETIC' AND s.sealed_at IS NOT NULL"""),
                {"cycle": cfg.cycle}).mappings().all()
            if len(snapshots) != 1:
                raise ValueError("Expected exactly one seeded SYNTHETIC snapshot for this cycle")
            snapshot = dict(snapshots[0])
            frame = pd.read_sql_query(text(QUERY.read_text()), con,
                params={"snapshot": snapshot["id"], "cycle": cfg.cycle, "course": cfg.course})
    finally:
        engine.dispose()
    if frame.empty or frame.isna().any().any() or frame.duplicated(KEYS + ["semester_index"]).any():
        raise ValueError("SQL extraction empty, null or duplicate academic/time keys")
    if (frame.students < 0).any() or frame.semester_index.nunique() < 3:
        raise ValueError("Insufficient or invalid historical data")
    snapshot.update(dataset_sha256=hashlib.sha256(frame.to_csv(index=False).encode()).hexdigest(),
        query_sha256=hashlib.sha256(QUERY.read_bytes()).hexdigest(), query_version="journey-history-v1")
    return frame, snapshot


def prepare(frame, snapshot):
    cutoff = int(frame.semester_index.max())
    train, evaluation = frame[frame.semester_index < cutoff].copy(), frame[frame.semester_index == cutoff].copy()
    future = frame[KEYS].drop_duplicates().reset_index(drop=True)
    future["semester_index"] = snapshot["target_index"]
    future["semester"] = snapshot["target_semester"]
    if not train.semester_index.max() < evaluation.semester_index.min() < future.semester_index.min():
        raise ValueError("Temporal leakage detected")
    return train, evaluation, future
