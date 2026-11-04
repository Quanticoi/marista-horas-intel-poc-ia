"""Explicit isolated integration test using existing PostgreSQL/RustFS, never live databases.

Run inside the application environment: python tests/c3_system.py.
Creates random test databases/bucket, starts temporary API processes, cleans its own resources.
This validates applications and persistence, not Docker networking/healthchecks.
"""
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path


def main():
    suffix = uuid.uuid4().hex[:12]
    databases = ["c3_test_app_"+suffix, "c3_test_mlflow_"+suffix]
    storage = "c3-test-"+suffix
    def free_port():
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0))
            return sock.getsockname()[1]
    tracking, intake_port, model_port, api_port = [free_port() for _ in range(4)]
    os.environ.update(APP_DB_NAME=databases[0], MLFLOW_DB_NAME=databases[1], S3_BUCKET=storage,
        MLFLOW_TRACKING_URI=f"http://127.0.0.1:{tracking}", INGESTION_URI=f"http://127.0.0.1:{intake_port}",
        INFERENCE_URI=f"http://127.0.0.1:{model_port}", API_URI=f"http://127.0.0.1:{api_port}",
        INGESTION_TOKEN=uuid.uuid4().hex, INFERENCE_TOKEN=uuid.uuid4().hex, API_TOKEN=uuid.uuid4().hex)
    import httpx
    from sqlalchemy import text
    from psycopg import sql
    from mlflow import MlflowClient
    from src.common.settings import database_url
    from src.persistence.db import engine
    from src.persistence.bootstrap import bootstrap, grants
    from src.data.storage import s3
    from src.workbench.sdk import connect, submit_dataset, test_dataset, train
    from src.mlops.registry import promote
    from alembic.config import Config
    from alembic import command
    processes = []
    logs = []
    report = {"status":"RUNNING", "checks":[], "test_suffix":suffix}
    Path(os.getenv("C3_REPORT","/tmp/c3-system.json")).write_text(json.dumps(report))
    def start(args, env=None):
        log = tempfile.TemporaryFile(mode="w+b")
        logs.append(log)
        process = subprocess.Popen([sys.executable,*args],env=env or os.environ.copy(),stdout=log,stderr=log)
        processes.append(process)
        return process
    def stop(process):
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    def wait(port, path, process):
        deadline = time.monotonic()+90
        while time.monotonic()<deadline:
            if process.poll() is not None:
                raise RuntimeError(f"Test service exited: port {port}")
            try:
                if httpx.get(f"http://127.0.0.1:{port}{path}",timeout=2).status_code==200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(.3)
        raise RuntimeError(f"Test readiness timeout: port {port}")
    def server(module, port, env=None):
        return start(["-m","uvicorn",module+":app","--host","127.0.0.1","--port",str(port)],env)
    try:
        bootstrap()
        command.upgrade(Config("alembic.ini"),"head")
        grants()
        s3().create_bucket(Bucket=storage)
        def tracking_server():
            env=os.environ.copy()
            env["MLFLOW_BACKEND_STORE_URI"]=database_url("mlflow").set(drivername="postgresql+psycopg2").render_as_string(hide_password=False)
            return start(["-m","mlflow","server","--host","127.0.0.1","--port",str(tracking),
                "--workers","1","--no-serve-artifacts","--default-artifact-root",f"s3://{storage}/mlflow"],env)
        tracking_process=tracking_server()
        wait(tracking,"/health",tracking_process)
        intake_process=server("src.ingestion.main",intake_port)
        wait(intake_port,"/ready",intake_process)
        connect()
        snapshot=submit_dataset(test_dataset())
        assert submit_dataset(test_dataset())["id"]==snapshot["id"]
        assert snapshot["row_count"]==350
        assert httpx.get(os.environ['INGESTION_URI']+'/v1/datasets').status_code==401
        report["checks"].append("intake authentication, dataset validation, idempotent persisted snapshot")
        first=train(snapshot["id"],"C1-CR1-P1")[0]
        assert MlflowClient().get_run(first["run_id"]).info.status=="FINISHED"
        assert not MlflowClient().get_registered_model(first["model_key"]).aliases
        report["checks"].append("SDK remote training, metrics, PostgreSQL, binary roundtrip from RustFS, no implicit approval")
        deployment=promote(first["model_key"],first["version"],"isolated-test","Isolated disposable integration test")
        env=dict(os.environ,MODEL_KEY=first["model_key"],REGISTERED_VERSION=first["version"],MODEL_DEPLOYMENT_ID=deployment)
        model_process=server("src.inference.model_api",model_port,env)
        wait(model_port,"/ready",model_process)
        api_process=server("src.api.main",api_port)
        wait(api_port,"/health",api_process)
        request=dict(cycle_id=snapshot["cycle_id"],snapshot_id=snapshot["id"],model_key=first["model_key"],requested_by="isolated-test")
        def predict(version):
            response=httpx.post(os.environ['API_URI']+'/v1/inference/predict',json=request,
                headers={"Authorization":"Bearer "+os.environ['API_TOKEN']},timeout=60)
            response.raise_for_status()
            prediction=response.json()
            assert prediction['registered_version']==version['version']
            assert prediction['mlflow_run_id']==version['run_id']
            assert prediction['artifact_sha256']==version['bundle_sha256']
            assert prediction['snapshot_id']==snapshot['id']
            return prediction
        predicted=predict(first)
        assert httpx.post(os.environ['INFERENCE_URI']+'/internal/predict',json={}).status_code==401
        report["checks"].append("dedicated API startup, token rejection, binary prediction and persisted full provenance")
        second=train(snapshot["id"],first["model_key"])[0]
        second_deployment=promote(second['model_key'],second['version'],'isolated-test','Isolated version update')
        assert httpx.get(os.environ['INFERENCE_URI']+'/ready').status_code==503
        stop(model_process)
        env.update(REGISTERED_VERSION=second['version'],MODEL_DEPLOYMENT_ID=second_deployment)
        model_process=server("src.inference.model_api",model_port,env)
        wait(model_port,"/ready",model_process)
        predict(second)
        report["checks"].append("new version approval, old API fails closed, explicit republication")
        stop(model_process)
        stop(tracking_process)
        subprocess.run([sys.executable,"-m","src.common.cli","migrate-mlflow"],check=True,capture_output=True,timeout=60)
        tracking_process=tracking_server()
        wait(tracking,"/health",tracking_process)
        model_process=server("src.inference.model_api",model_port,env)
        wait(model_port,"/ready",model_process)
        predict(second)
        report["checks"].append("MLflow schema upgrade and recreated processes; PostgreSQL metadata and RustFS binaries survive")
        with engine('mlflow').connect() as con:
            assert con.execute(text("SELECT count(*) FROM public.runs")).scalar_one()==2
        report.update(status="PASS",runs=2,versions=2,model_key=first['model_key'],code_version=predicted['code_version'])
    except Exception as error:
        report.update(status="FAIL",error=type(error).__name__,detail=str(error))
        raise
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                stop(process)
        # Only random resources created by this invocation; never application databases/bucket.
        for role in ('app','readonly','migration','mlflow'):
            engine(role).dispose()
        with engine('admin').connect().execution_options(isolation_level='AUTOCOMMIT') as con:
            db=con.connection.driver_connection
            for name in databases:
                assert name.endswith(suffix) and name.startswith('c3_test_')
                db.execute(sql.SQL('DROP DATABASE IF EXISTS {} WITH (FORCE)').format(sql.Identifier(name)))
        client=s3()
        try:
            for page in client.get_paginator('list_objects_v2').paginate(Bucket=storage):
                if page.get('Contents'):
                    client.delete_objects(Bucket=storage,Delete={'Objects':[{'Key':o['Key']} for o in page['Contents']]})
            client.delete_bucket(Bucket=storage)
        except client.exceptions.NoSuchBucket:
            pass
        for log in logs:
            log.close()
        output=Path(os.getenv('C3_REPORT','/tmp/c3-system.json'))
        output.write_text(json.dumps(report,indent=2))
        print(json.dumps(report))


if __name__=='__main__':
    main()
