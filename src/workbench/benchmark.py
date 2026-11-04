"""Measured 30 real trainings and a separate 500-identity catalog exercise."""
import json
import time
import resource
from pathlib import Path
from uuid import uuid4
from sqlalchemy import text
from src.common.lineage import utcnow,manifest,put_manifest
from src.workbench.journey_config import Settings,sql_engine
from src.workbench.sdk import train,source_version
from src.data.journey import extract
from src.persistence.lineage import entity,edge


def main():
    cfg=Settings.load()
    _,snapshot=extract(cfg)
    campaign_id=str(uuid4())
    start=time.monotonic(); cpu=time.process_time()
    versions=train(snapshot["id"])
    if len(versions)!=30:
        raise ValueError("Expected 30 actual catalog models")
    training=dict(actual_trained=len(versions),seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,errors=0,versions=versions)
    start=time.monotonic(); cpu=time.process_time()
    identities=[f"DEMO-INVENTORY-{i:04d}" for i in range(500)]
    engine=sql_engine(cfg.application)
    try:
        with engine.begin() as con:
            root=entity(con,"inventory-campaign",campaign_id,{"source_type":"DEMO","actual_trained":False})
            for key in identities:
                node=entity(con,"model-identity",key,{"source_type":"DEMO","registered":False})
                edge(con,node,root,"CONTRIBUTED_TO")
            count=con.execute(text("SELECT count(*) FROM planning.lineage_edges WHERE child_id=:id"),{"id":root}).scalar_one()
            assert count==500
    finally:
        engine.dispose()
    storage=put_manifest(f"lineage/poc/planilha-turmas/campaigns/{campaign_id}/manifest.json",
        manifest("inventory-campaign",{},utcnow(),training_campaign_id=campaign_id,model_keys=identities,
                 registered_models=0,executed_trainings=0))
    inventory=dict(identities=count,registered_models=0,trained_models=0,api_containers=0,simultaneously_loaded=0,
        seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,errors=0,storage=storage)
    result=dict(timestamp_utc=utcnow(),code_version=source_version(),environment="poc",training_campaign_id=campaign_id,
                training30=training,inventory500=inventory,limitations="RSS/CPU do processo; não mede capacidade simultânea de 500 modelos")
    Path("/reports/model-benchmark.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps({"training30":{k:v for k,v in training.items() if k!="versions"},"inventory500":inventory}))


if __name__=="__main__":
    main()
