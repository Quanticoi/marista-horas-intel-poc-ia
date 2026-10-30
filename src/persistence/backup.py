"""Logical dumps in S3. Restore only creates isolated databases, never overwrites."""
import hashlib
import json
import os
import re
import subprocess
import tempfile
import uuid
from datetime import datetime,timezone
from pathlib import Path
from psycopg import sql
from src.persistence.db import engine
from src.common.settings import required
from src.data.storage import s3,bucket


def pg_environment():
    return dict(os.environ,PGHOST=os.getenv("DB_HOST","postgres"),
                PGUSER="postgres",PGPASSWORD=required("POSTGRES_PASSWORD"),PGCONNECT_TIMEOUT="10")


def backup():
    prefix="backups/"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")+"-"+uuid.uuid4().hex[:8]
    manifest={"format":1,"databases":{},"consistency":"per-database; pause writes for cross-database consistency"}
    with tempfile.TemporaryDirectory() as directory:
        for database in ("planejamento_db","mlflow_db"):
            path=Path(directory)/(database+".dump")
            subprocess.run(["pg_dump","--format=custom","--no-owner","--no-acl","--file",str(path),database],
                           env=pg_environment(),check=True,timeout=600,capture_output=True)
            manifest["databases"][database]=hashlib.sha256(path.read_bytes()).hexdigest()
            s3().upload_file(str(path),bucket(),f"{prefix}/{database}.dump")
        s3().put_object(Bucket=bucket(),Key=prefix+"/manifest.json",Body=json.dumps(manifest).encode())
    return prefix


def restore(prefix,target_prefix):
    if not re.fullmatch(r"restore_[a-z0-9_]{1,24}",target_prefix):
        raise ValueError("New database prefix must match restore_[a-z0-9_]{1,24}")
    if not re.fullmatch(r"backups/[A-Za-z0-9_-]+",prefix):
        raise ValueError("Invalid backup prefix")
    manifest=json.loads(s3().get_object(Bucket=bucket(),Key=prefix+"/manifest.json")["Body"].read())
    if manifest.get("format")!=1 or set(manifest["databases"])!={"planejamento_db","mlflow_db"}:
        raise ValueError("Invalid backup manifest")
    with tempfile.TemporaryDirectory() as directory:
        for database in manifest["databases"]:
            target=target_prefix+"_"+database
            path=Path(directory)/(database+".dump")
            s3().download_file(bucket(),f"{prefix}/{database}.dump",str(path))
            if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest["databases"][database]:
                raise ValueError("Backup checksum mismatch")
            with engine("admin").connect().execution_options(isolation_level="AUTOCOMMIT") as con:
                db=con.connection.driver_connection
                if db.execute("SELECT 1 FROM pg_database WHERE datname=%s",(target,)).fetchone():
                    raise ValueError("Restore target already exists; refusing overwrite")
                db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(target)))
                db.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(sql.Identifier(target)))
            subprocess.run(["pg_restore","--exit-on-error","--no-owner","--no-acl","--dbname",target,str(path)],
                           env=pg_environment(),check=True,timeout=600,capture_output=True)
            print(f"RESTORED {target}; isolated, no application cutover")
