"""Operations entrypoint for Docker Compose tools containers."""
import argparse
import json
import sys


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("action",choices=["bootstrap","migrate","migrate-mlflow","buckets","validate","seed","train","retrain",
        "evaluate","promote","reconcile","predict","monitor","recover","worker-ready","test","e2e","backup","restore","diagnose"])
    parser.add_argument("arguments",nargs="*")
    args=parser.parse_args()
    a=args.arguments
    if args.action=="diagnose":
        from src.dashboard.main import logs
        print(json.dumps(logs(limit=100,q=""),default=str))
    elif args.action=="bootstrap":
        from src.persistence.bootstrap import bootstrap
        bootstrap()
    elif args.action=="migrate":
        from alembic.config import Config
        from alembic import command
        from src.persistence.bootstrap import grants
        command.upgrade(Config("alembic.ini"),"head")
        grants()
    elif args.action=="migrate-mlflow":
        from src.persistence.mlflow_schema import upgrade
        upgrade()
    elif args.action=="buckets":
        from src.data.storage import s3,bucket
        from botocore.exceptions import ClientError
        client=s3()
        try:
            client.head_bucket(Bucket=bucket())
        except ClientError as error:
            if error.response["ResponseMetadata"]["HTTPStatusCode"]!=404:
                raise
            client.create_bucket(Bucket=bucket())
        client.put_bucket_versioning(Bucket=bucket(),VersioningConfiguration={"Status":"Enabled"})
        # Actual compatibility check, not an assumed MinIO/RustFS equivalence.
        client.put_object(Bucket=bucket(),Key="checks/compatibility",Body=b"pucpr")
        assert client.get_object(Bucket=bucket(),Key="checks/compatibility")["Body"].read()==b"pucpr"
    elif args.action=="validate":
        from src.common.validation import validate_environment
        validate_environment(require_gold=False)
    elif args.action=="seed":
        from src.data.pipeline import seed
        print(json.dumps({"snapshot_id":seed()}))
    elif args.action in ("train","retrain"):
        from src.training.pipeline import train
        from src.persistence.db import rows
        snapshot=a[0] if a else rows("SELECT id FROM planning.dataset_snapshots WHERE sealed_at IS NOT NULL ORDER BY created_at DESC LIMIT 1")[0]["id"]
        print(json.dumps(train(snapshot, model_key=a[1] if len(a)>1 else None)))
    elif args.action=="evaluate":
        from src.monitoring.quality import evaluate
        if len(a)!=1: parser.error("evaluate <cycle_id>")
        print(json.dumps(evaluate(a[0]),default=str))
    elif args.action=="promote":
        from src.mlops.registry import promote
        if len(a)!=4: parser.error("promote <model_key> <version> <actor> <reason>")
        print(promote(*a))
    elif args.action=="reconcile":
        from src.mlops.registry import reconcile
        if len(a)!=3: parser.error("reconcile <model_key> <actor> <reason>")
        reconcile(*a)
    elif args.action=="predict":
        import os,httpx
        if len(a)!=3: parser.error("predict <cycle_id> <snapshot_id> <model_key>")
        response=httpx.post(os.environ["API_URI"]+"/v1/inference/predict",timeout=120,
            headers={"Authorization":"Bearer "+os.environ["API_TOKEN"]},json=dict(cycle_id=a[0],snapshot_id=a[1],model_key=a[2],requested_by="operator"))
        response.raise_for_status()
        print(response.text)
    elif args.action=="monitor":
        from src.monitoring.quality import monitor
        print(json.dumps(monitor(),default=str))
    elif args.action=="recover":
        from src.workers.tasks import recover
        recover()
    elif args.action=="worker-ready":
        from src.workers.tasks import app
        import socket
        if not app.control.ping(destination=["celery@"+socket.gethostname()],timeout=5):
            raise RuntimeError("Worker not responding")
    elif args.action in ("test","e2e"):
        import pytest
        paths=["tests/unit"] if args.action=="test" else ["tests/unit","tests/integration","tests/e2e"]
        code=pytest.main(["-q",*paths,"--junitxml=/tmp/test-results.xml"])
        if args.action=="e2e":
            from src.data.storage import s3,bucket
            from pathlib import Path
            from datetime import datetime,timezone
            report=f"# E2E\n\nUTC: {datetime.now(timezone.utc).isoformat()}\n\npytest: {'PASS' if code==0 else 'FAIL'} (exit {code})\n\nPVC restart/backup restore acceptance requires explicit host checks; see docs/operations/ACCEPTANCE.md.\n"
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
            for prefix in ("reports",f"reports/{stamp}"):
                s3().put_object(Bucket=bucket(),Key=prefix+"/e2e-report.md",Body=report.encode())
                s3().put_object(Bucket=bucket(),Key=prefix+"/test-results.xml",Body=Path("/tmp/test-results.xml").read_bytes())
            print(report)
        sys.exit(code)
    elif args.action in ("backup","restore"):
        from src.persistence.backup import backup,restore
        if args.action=="backup": print(backup())
        else:
            if len(a)!=2: parser.error("restore <backup-prefix> <new_database_prefix>")
            restore(*a)


if __name__=="__main__":
    main()
