"""Read-only inventory for the external reset controller; no secrets in output."""
import json
import httpx
from sqlalchemy import create_engine,text,inspect
from src.common.settings import database_url,required
from src.data.storage import s3,bucket


def inventory():
    databases={}
    database_names=[]
    for role in ("app","mlflow"):
        engine=create_engine(database_url(role),hide_parameters=True)
        tables={}
        try:
            with engine.connect() as con:
                if role=="app":
                    database_names=list(con.execute(text("SELECT datname FROM pg_database WHERE NOT datistemplate ORDER BY datname")).scalars())
                schema="planning" if role=="app" else "public"
                for name in sorted(inspect(engine).get_table_names(schema=schema)):
                    quoted=engine.dialect.identifier_preparer.quote(name)
                    # Ordered row hashes detect changes even when counts stay the same.
                    row=con.execute(text(f'''SELECT count(*) AS count,
                        md5(COALESCE(string_agg(h,',' ORDER BY h),'')) AS digest
                        FROM (SELECT md5(row_to_json(t)::text) AS h FROM {schema}.{quoted} t) q''')).mappings().one()
                    tables[name]=dict(row)
        finally:
            engine.dispose()
        databases["planejamento_db" if role=="app" else "mlflow_db"]=tables
    client=s3()
    objects=[]
    for page in client.get_paginator("list_object_versions").paginate(Bucket=bucket()):
        for kind in ("Versions","DeleteMarkers"):
            for item in page.get(kind,[]):
                objects.append({"key":item["Key"],"version":item["VersionId"],"kind":kind,"size":item.get("Size",0)})
    buckets=sorted(item["Name"] for item in client.list_buckets()["Buckets"])
    response=httpx.get("http://rabbitmq:15672/api/queues",auth=("poc",required("RABBITMQ_PASSWORD")),timeout=15)
    response.raise_for_status()
    queues=sorted([{"name":q["name"],"vhost":q["vhost"],"messages":q.get("messages",0)}
                   for q in response.json() if q.get("durable")],key=lambda q:(q["vhost"],q["name"]))
    return dict(databases=databases,database_names=database_names,buckets=buckets,queues=queues,
                bucket=bucket(),versioning=client.get_bucket_versioning(Bucket=bucket()).get("Status","Disabled"),
                objects=sorted(objects,key=lambda x:(x["key"],x["version"])))


if __name__=="__main__":
    print(json.dumps(inventory(),sort_keys=True))
