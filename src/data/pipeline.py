import hashlib
import io
import json
import uuid
from datetime import date
import pandas as pd
from sqlalchemy import text
from src.common.settings import config
from src.data.synthetic import generate, identity, validate
from src.data.storage import s3, bucket
from src.persistence.db import engine, rows, audit


def seed():
    with engine().connect() as lock:
        lock.execute(text("SELECT pg_advisory_lock(hashtext('synthetic-seed'))"))
        lock.commit()
        try:
            return _seed()
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(hashtext('synthetic-seed'))"))
            lock.commit()


def _seed():
    cfg = config("training")
    records = generate(cfg["seed"], cfg["semesters"], cfg["start_year"])
    return persist_dataset(records, cfg, "SYNTHETIC")


def ingest(records, cfg, source):
    # Serialize snapshot/catalog creation, including retries with identical content.
    with engine().connect() as lock:
        lock.execute(text("SELECT pg_advisory_lock(hashtext('synthetic-seed'))"))
        lock.commit()
        try:
            return persist_dataset(records, cfg, source)
        finally:
            lock.execute(text("SELECT pg_advisory_unlock(hashtext('synthetic-seed'))"))
            lock.commit()


def persist_dataset(records, cfg, source):
    validate(records, date.fromisoformat(cfg["as_of_date"]))
    identity_payload = {"records":records,"configuration":cfg,"schema_version":"1.0"}
    if source != "SYNTHETIC":
        identity_payload["source"] = source
    payload = json.dumps(identity_payload, sort_keys=True).encode()
    snapshot_id = identity(hashlib.sha256(payload).hexdigest())
    existing = rows("SELECT id FROM planning.dataset_snapshots WHERE id=:id", {"id": snapshot_id})
    if existing:
        return str(snapshot_id)
    client = s3()
    prefix = f"snapshots/{snapshot_id}"
    frame = pd.DataFrame(records)
    hashes = {}
    for layer in ("raw", "bronze", "silver", "gold"):
        buffer = io.BytesIO()
        frame.to_parquet(buffer, index=False)
        content = buffer.getvalue()
        key = f"{prefix}/{layer}.parquet"
        # Immutable write: a retry must match bytes; never overwrite different content.
        try:
            old = client.get_object(Bucket=bucket(), Key=key)["Body"].read()
            if old != content:
                raise RuntimeError("Immutable snapshot conflict")
        except client.exceptions.NoSuchKey:
            client.put_object(Bucket=bucket(), Key=key, Body=content)
        hashes[layer] = hashlib.sha256(content).hexdigest()
    manifest = dict(snapshot_id=str(snapshot_id), schema_version="1.0", source=source,
                    as_of_date=cfg["as_of_date"], row_count=len(records), hashes=hashes)
    manifest_bytes = json.dumps(manifest,sort_keys=True).encode()
    try:
        old = client.get_object(Bucket=bucket(), Key=f"{prefix}/manifest.json")["Body"].read()
        if old != manifest_bytes:
            raise RuntimeError("Immutable manifest conflict")
    except client.exceptions.NoSuchKey:
        client.put_object(Bucket=bucket(), Key=f"{prefix}/manifest.json", Body=manifest_bytes)
    cycle_id = identity(f"cycle-{cfg['target_year']}-{cfg['target_semester']}")
    with engine().begin() as con:
        con.execute(text("""INSERT INTO planning.academic_cycles(id,cycle_code,target_year,target_semester,status)
            VALUES (:id,:code,:year,:semester,'READY') ON CONFLICT DO NOTHING"""),
            dict(id=cycle_id, code=f"{cfg['target_year']}-{cfg['target_semester']}",
                 year=cfg["target_year"], semester=cfg["target_semester"]))
        con.execute(text("""INSERT INTO planning.dataset_snapshots
            (id,snapshot_key,cycle_id,layer,bucket,object_prefix,schema_version,sha256,row_count,source_reference,as_of_date,sealed_at)
            VALUES (:id,:key,:cycle,'GOLD',:bucket,:prefix,'1.0',:sha,:count,:source,:asof,NULL)"""),
            dict(id=snapshot_id, key=f"synthetic-{snapshot_id}", cycle=cycle_id, bucket=bucket(),
                 prefix=prefix, sha=hashlib.sha256(manifest_bytes).hexdigest(), count=len(records), asof=cfg["as_of_date"], source=source))
        for key, group in frame.groupby("model_key"):
            row = group.iloc[0].to_dict()
            campus, course, period = key.split("-")
            for query, params in [
                ("INSERT INTO planning.campuses(id,code,name) VALUES (:id,:code,:code) ON CONFLICT DO NOTHING",
                 dict(id=row["campus_id"], code=campus)),
                ("INSERT INTO planning.courses(id,campus_id,code,name) VALUES (:id,:parent,:code,:code) ON CONFLICT DO NOTHING",
                 dict(id=row["course_id"], parent=row["campus_id"], code=course)),
                ("INSERT INTO planning.academic_periods(id,course_id,period_number) VALUES (:id,:parent,:number) ON CONFLICT DO NOTHING",
                 dict(id=row["period_id"], parent=row["course_id"], number=int(period[1:]))),
                ("""INSERT INTO planning.model_catalog(id,model_key,campus_id,course_id,period_id,mlflow_registered_name)
                   VALUES (:id,:key,:campus_id,:course_id,:period_id,:key) ON CONFLICT DO NOTHING""",
                 dict(id=identity("model-"+key), key=key, **{c: row[c] for c in ("campus_id","course_id","period_id")}))]:
                con.execute(text(query), params)
            for number in range(1, 4):
                disc = identity(f"{key}-D{number}")
                con.execute(text("""INSERT INTO planning.disciplines(id,course_id,code,name,credits,modulation_limit)
                    VALUES (:id,:course,:code,:code,4,40) ON CONFLICT DO NOTHING"""),
                    dict(id=disc, course=row["course_id"], code=f"{period}-D{number}"))
                con.execute(text("INSERT INTO planning.period_disciplines VALUES (:period,:disc,true) ON CONFLICT DO NOTHING"),
                    dict(period=row["period_id"], disc=disc))
        for row in records:
            con.execute(text("""INSERT INTO planning.historical_enrollments
              (campus_id,course_id,period_id,reference_year,reference_semester,regular_students,dependency_students,elective_students,snapshot_id)
              VALUES (:campus_id,:course_id,:period_id,:reference_year,:reference_semester,:regular_students,:dependency_students,:elective_students,:snapshot_id)"""),
              dict(row, snapshot_id=snapshot_id))
        con.execute(text("UPDATE planning.dataset_snapshots SET sealed_at=now() WHERE id=:id"), {"id":snapshot_id})
        audit(con, "seed", "SNAPSHOT_SEALED", "snapshot", snapshot_id, str(snapshot_id), manifest)
    return str(snapshot_id)


def load(snapshot_id):
    snapshot = rows("SELECT * FROM planning.dataset_snapshots WHERE id=:id AND sealed_at IS NOT NULL", {"id": snapshot_id})
    if not snapshot:
        raise ValueError("Sealed snapshot not found")
    snapshot = snapshot[0]
    client = s3()
    manifest_bytes = client.get_object(Bucket=snapshot["bucket"], Key=f"{snapshot['object_prefix']}/manifest.json")["Body"].read()
    if hashlib.sha256(manifest_bytes).hexdigest() != snapshot["sha256"]:
        raise ValueError("Manifest checksum mismatch")
    manifest = json.loads(manifest_bytes)
    if manifest["snapshot_id"] != str(snapshot["id"]) or manifest["schema_version"] != snapshot["schema_version"]:
        raise ValueError("Manifest provenance mismatch")
    data = client.get_object(Bucket=snapshot["bucket"], Key=f"{snapshot['object_prefix']}/gold.parquet")["Body"].read()
    if hashlib.sha256(data).hexdigest() != manifest["hashes"]["gold"]:
        raise ValueError("Gold checksum mismatch")
    frame = pd.read_parquet(io.BytesIO(data))
    if len(frame) != snapshot["row_count"] or len(frame) != manifest["row_count"]:
        raise ValueError("Snapshot row count mismatch")
    validate(frame.to_dict("records"), snapshot["as_of_date"])
    return frame
