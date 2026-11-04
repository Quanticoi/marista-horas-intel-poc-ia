import json
from pathlib import Path
from uuid import uuid4
import pytest
from sqlalchemy import text
from src.workbench.journey_config import Settings,sql_engine
from src.workbench.contract_review import preflight,fetch_payload,reconcile,request
from src.common.lineage import put_manifest


@pytest.fixture
def journey():
    path=Path("/reports/journey-latest.json")
    if not path.exists():
        pytest.skip("Execute notebook01 first")
    return json.loads(path.read_text())


def test_http_contract_and_reverse_navigation(journey):
    cfg=Settings.load()
    preflight(cfg)
    pages,offers=fetch_payload(cfg,journey["execution_id"],17)
    assert len(pages)>1
    reconcile(cfg,journey["execution_id"],pages,offers)
    for kind,value in (("proposal",journey["execution_id"]),("run",journey["run_id"]),
                       ("model",journey["model_name"]),("snapshot",journey["snapshot_id"])):
        r=request(cfg,f"/v1/lineage?kind={kind}&external_id={value}")
        r.raise_for_status()
        assert any(row["proposal_id"]==journey["execution_id"] for row in r.json()["items"])


def test_immutable_manifest_retry_and_collision():
    key=f"lineage/poc/planilha-turmas/checks/{uuid4()}/manifest.json"
    first=put_manifest(key,{"status":"diagnostic","schema":"1"})
    assert put_manifest(key,{"schema":"1","status":"diagnostic"})==first
    with pytest.raises(ValueError,match="collision"):
        put_manifest(key,{"status":"changed"})


def test_lineage_append_only(journey):
    cfg=Settings.load(); engine=sql_engine(cfg.application)
    try:
        for table,column in (("proposal_model_usage","proposal_id"),("proposal_contract_evidence","proposal_id")):
            with pytest.raises(Exception):
                with engine.begin() as con:
                    con.execute(text(f"DELETE FROM planning.{table} WHERE {column}=:id"),{"id":journey["execution_id"]})
    finally:
        engine.dispose()
