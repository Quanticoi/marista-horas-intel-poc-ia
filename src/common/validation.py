import os
import httpx
from src.persistence.db import rows
from src.data.storage import s3, bucket


def validate_environment(require_gold=True):
    if not os.getenv("READONLY_PASSWORD"):
        from src.workbench.sdk import connect, intake
        result = connect()
        if require_gold and not intake("GET", "/v1/datasets"):
            raise RuntimeError("Submit a dataset through intake first")
        return result
    results={}
    checks={
        "kernel": lambda: __import__("ipykernel"),
        "postgres_readonly": lambda: rows("SELECT 1",role="readonly"),
        "mlflow": lambda: httpx.get(os.environ["MLFLOW_TRACKING_URI"]+"/health",timeout=10).raise_for_status(),
        "rustfs": lambda: s3().head_bucket(Bucket=bucket()),
        "api": lambda: httpx.get(os.environ["API_URI"]+"/ready",timeout=20).raise_for_status(),
    }
    def permissions():
        result=rows("SELECT has_table_privilege(current_user,'planning.audit_events','SELECT') AS read, has_table_privilege(current_user,'planning.audit_events','UPDATE') AS write",role="readonly")[0]
        assert result["read"] and not result["write"]
    checks["permissions"]=permissions
    if require_gold:
        def gold():
            snapshots=rows("SELECT id FROM planning.dataset_snapshots WHERE layer='GOLD' AND sealed_at IS NOT NULL LIMIT 1",role="readonly")
            assert snapshots, "Execute seed primeiro"
        checks["gold"]=gold
    for name,check in checks.items():
        try:
            check()
            results[name]="PASS"
        except Exception as error:
            results[name]="FAIL: "+type(error).__name__
        print(f"{results[name]} {name}")
    if any(value.startswith("FAIL") for value in results.values()):
        raise RuntimeError("Environment validation failed")
    return results
