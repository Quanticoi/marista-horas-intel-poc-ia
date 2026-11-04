"""Read-only HTTP + SQL + Registry + Object Store contract review."""
import json
from pathlib import Path
from uuid import UUID, uuid4
import httpx
import mlflow
from sqlalchemy import text
from src.api.proposal_contract import ApplicationView
from src.common.lineage import sha256, utcnow
from src.common.settings import required
from src.workbench.journey_config import sql_engine
from src.workbench.verification import verify_model_storage, verify_proposal_sql


def request(cfg, path, authorized=True):
    headers = {"Authorization":"Bearer "+required("API_TOKEN")} if authorized else {}
    return httpx.get(cfg.api+path,headers=headers,timeout=cfg.timeout)


def preflight(cfg):
    mlflow.set_tracking_uri(cfg.tracking)
    response = request(cfg,"/ready")
    response.raise_for_status()
    schema = request(cfg,"/openapi.json")
    schema.raise_for_status()
    assert "/v1/proposals/{execution_id}/application-view" in schema.json()["paths"]
    denied = request(cfg,"/v1/proposals?cycle="+cfg.cycle,False)
    assert denied.status_code == 401
    client = mlflow.MlflowClient()
    client.search_experiments(max_results=1)
    return [{"dependency":"API/OpenAPI/auth negative/MLflow SDK","status":"PASS"}]


def candidates(cfg):
    engine = sql_engine(cfg.source,cfg.timeout)
    try:
        with engine.connect() as con:
            return [dict(r) for r in con.execute(text("""SELECT execution_id,generated_at,model_name,
                model_version,g.status,row_count FROM planning.proposal_generations g
                JOIN planning.academic_cycles c ON c.id=g.cycle_id
                WHERE c.cycle_code=:cycle ORDER BY generated_at DESC,execution_id LIMIT 50"""),
                {"cycle":cfg.cycle}).mappings()]
    finally:
        engine.dispose()


def fetch_payload(cfg, execution_id, page_size=100, max_rows=10000):
    UUID(str(execution_id))
    if not 1<=page_size<=500 or not 1<=max_rows<=10000:
        raise ValueError("Invalid pagination bounds")
    pages, offers = [], []
    for offset in range(0,max_rows,page_size):
        response = request(cfg,f"/v1/proposals/{execution_id}/application-view?limit={page_size}&offset={offset}")
        response.raise_for_status()
        payload = response.json()
        ApplicationView.model_validate(payload)
        body = {k:v for k,v in payload.items() if k!="payload_sha256"}
        if sha256(body)!=payload["payload_sha256"]:
            raise ValueError("HTTP payload integrity mismatch")
        if pages and payload["total_rows"]!=pages[0]["total_rows"]:
            raise ValueError("Pagination changed during read")
        pages.append(payload)
        offers.extend(payload["offers"])
        if len(offers)>=payload["total_rows"]:
            break
    if len(offers)!=pages[0]["total_rows"] or len({o["offer_id"] for o in offers})!=len(offers):
        raise ValueError("Incomplete or duplicate HTTP pagination; increase max_rows explicitly")
    return pages,offers


def reconcile(cfg, execution_id, pages, offers):
    response = request(cfg,f"/v1/proposals/{execution_id}")
    response.raise_for_status()
    header = response.json()
    expected = [{**{k:o[k] for k in ("course_id","period_id","discipline_id","forecast_raw","human_adjustment")},
                 "proposed_students":o["students"]["total"],"proposed_groups":o["modulation"]["proposed_groups"]} for o in offers]
    sql = verify_proposal_sql(cfg,execution_id,header,expected)
    from src.workbench.sdk import intake
    snapshot = intake("GET",f"/v1/datasets/{header['snapshot_id']}")
    if snapshot["sha256"]!=pages[0]["lineage"]["snapshot_sha256"]:
        raise ValueError("Snapshot SQL/Object Store integrity mismatch")
    usages=pages[0]["lineage"]["model_usages"]
    if usages and all(u["provenance_status"]=="VERIFIED" for u in usages) and any(not o["source_model_keys"] for o in offers):
        raise ValueError("Verified proposal contains an offer without model origin")
    storage = []
    for usage in pages[0]["lineage"]["model_usages"]:
        trace = dict(model_name=usage["registered_model_name"],model_version=usage["model_version"],run_id=usage["run_id"],
                     model_uri=f"models:/{usage['registered_model_name']}/{usage['model_version']}")
        proof = verify_model_storage(trace)
        if usage["artifact_sha256"] and usage["artifact_sha256"] != next(p["sha256"] for p in proof if p["key"].endswith("/model.pkl")):
            raise ValueError("Lineage artifact hash differs from storage")
        storage.extend(proof)
    assert request(cfg,f"/v1/proposals/{uuid4()}/application-view").status_code==404
    negative = dict(pages[0],schema_version="unsupported")
    try:
        ApplicationView.model_validate(negative)
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported schema accepted")
    modified = dict(pages[0],status="CORRUPTED")
    assert sha256({k:v for k,v in modified.items() if k!="payload_sha256"})!=pages[0]["payload_sha256"]
    return dict(sql=sql,storage=storage,snapshot={"snapshot_id":header["snapshot_id"],"sha256":snapshot["sha256"],"status":"PASS"},
                negative_checks=["401","404","unsupported-schema","altered-payload-hash"])


def report(execution_id,pages,evidence,directory="/reports"):
    from src.workbench.sdk import source_version
    report = dict(test_id="AC08-09",timestamp_utc=utcnow(),environment="poc",code_version=source_version(),
        execution_id=str(execution_id),proposal_id=str(execution_id),status="PASS",contract_status=pages[0]["contract_status"],
        http_pages=pages,evidence=evidence,limitations="DEMO técnico; regras NOT_EVALUATED não homologadas")
    root=Path(directory)
    root.mkdir(parents=True,exist_ok=True)
    path=root/f"inference-contract-{execution_id}.json"
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    path.with_suffix(".md").write_text(f"# Contrato de inferência\n\n{report['timestamp_utc']} — {execution_id}\n\nPASS técnico. {report['contract_status']}\n\n"+
        "\n".join(f"- {r['rule_id']}: {r['status']} — {r['reason']}" for r in pages[0]["validation"]),encoding="utf-8")
    return str(path)


def invoke_demo(cfg,execution_id):
    from src.data.journey import extract,prepare,FEATURES
    header=request(cfg,f"/v1/proposals/{execution_id}")
    header.raise_for_status()
    data=header.json()
    frame,snapshot=extract(cfg)
    if str(snapshot["id"])!=data["snapshot_id"]:
        raise ValueError("Selected proposal does not match configured SQL snapshot")
    _,_,future=prepare(frame,snapshot)
    response=httpx.post(cfg.inference+"/internal/draft/predict",timeout=120,
        headers={"Authorization":"Bearer "+required("INFERENCE_TOKEN")},
        json=dict(execution_id=str(execution_id),snapshot_id=data["snapshot_id"],model_name=data["model_name"],
                  model_version=data["model_version"],run_id=data["run_id"],records=future[FEATURES].to_dict("records")))
    response.raise_for_status()
    return response.json()
