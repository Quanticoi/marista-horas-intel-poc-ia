"""Internal reset action, invoked only by the scoped host controller after quiescence."""
import os
import json
import httpx
from psycopg import sql
from src.persistence.db import engine
from src.data.storage import s3,bucket
from src.common.settings import required
from src.common.settings import database_url
from src.persistence.reset_policy import partition_tables
from sqlalchemy import create_engine,inspect


def reset():
    if not os.getenv("POC_RESET_PLAN_ID"):
        raise ValueError("External validated reset plan required")
    mode=os.getenv('POC_RESET_MODE','reset-data')
    if mode not in ('reset-data','reset-experiments'):
        raise ValueError('Unsupported reset mode')
    # Preserve source rows in their original database. No CASCADE: a new foreign
    # dependency must fail rather than silently truncate an unlisted source.
    if mode=='reset-experiments':
        admin=create_engine(database_url('admin').set(database='planejamento_db'),hide_parameters=True)
        try:
            with admin.begin() as connection:
                _,remove=partition_tables(inspect(connection).get_table_names(schema='planning'))
                statement=sql.SQL('TRUNCATE TABLE {} RESTART IDENTITY').format(sql.SQL(', ').join(
                    sql.Identifier('planning',name) for name in remove))
                connection.connection.driver_connection.execute(statement)
        finally:
            admin.dispose()
    client=s3()
    # Dedicated bucket: preserve historical backups; only inventoried POC prefixes.
    prefixes=("mlflow/","snapshots/","lineage/","checks/","reports/","datasets/")
    for page in client.get_paginator("list_object_versions").paginate(Bucket=bucket()):
        objects=[{"Key":v["Key"],"VersionId":v["VersionId"]} for kind in ("Versions","DeleteMarkers")
                 for v in page.get(kind,[]) if (not v["Key"].startswith('backups/') if mode=='reset-experiments' else v["Key"].startswith(prefixes))]
        if objects:
            response=client.delete_objects(Bucket=bucket(),Delete={"Objects":objects,"Quiet":True})
            if response.get("Errors"):
                raise RuntimeError("Scoped object removal incomplete")
    with engine("admin").connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        db=connection.connection.driver_connection
        for database in (("mlflow_db",) if mode=='reset-experiments' else ("planejamento_db","mlflow_db")):
            db.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s AND pid<>pg_backend_pid()",(database,))
            db.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(database)))
    # RabbitMQ instance is exclusive, verified by host controller. Recreate only default vhost.
    with httpx.Client(base_url="http://rabbitmq:15672",auth=("poc",required("RABBITMQ_PASSWORD")),timeout=30) as http:
        http.delete("/api/vhosts/%2F").raise_for_status()
        http.put("/api/vhosts/%2F",json={}).raise_for_status()
        http.put("/api/permissions/%2F/poc",json={"configure":".*","write":".*","read":".*"}).raise_for_status()
    print(json.dumps({"reset_data":"completed","plan_id":os.environ["POC_RESET_PLAN_ID"]}))


if __name__=="__main__":
    reset()
