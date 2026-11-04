"""External opt-in controller. Import and preview never delete application data."""
import argparse
from contextlib import contextmanager
from datetime import datetime,timezone,timedelta
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT=Path(__file__).resolve().parents[2]
REPORTS=ROOT/"artifacts/reports/reset"
PHRASE="APAGAR TODOS OS DADOS DA POC MARISTA"
SCOPES={"marista":ROOT/"compose.yaml",
        "marista-correcoes-isolated":ROOT/".runtime/correcoes-isolated/compose.json"}


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":")).encode()).hexdigest()


def run(args):
    result=subprocess.run(args,capture_output=True,text=True,timeout=600)
    if result.returncode:
        # Docker/SQL errors may include environment. Never emit raw stderr.
        raise RuntimeError("Command failed: "+" ".join(args[:3])+f" (exit {result.returncode}); inspect scoped Docker logs")
    return result.stdout


def compose(project,*args):
    return run(["docker","compose","--env-file",str(ROOT/".env"),"-f",str(SCOPES[project]),"-p",project,*args])


def preserved():
    paths=[ROOT/".env",*sorted((ROOT/"notebooks").glob("*.ipynb")),*sorted((ROOT/"workspace").rglob("*.ipynb"))]
    for folder in (ROOT/"backups",ROOT/".runtime/migration"):
        if folder.exists():
            paths.extend(p for p in folder.rglob("*") if p.is_file())
    isolated=ROOT/".runtime/correcoes-isolated/workspace"
    if isolated.exists():
        paths.extend(isolated.rglob("*.ipynb"))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}


def validate_scope(environment,project):
    if environment!="poc" or project not in SCOPES:
        raise ValueError("Reset allowed only for explicitly allowlisted POC scope")
    config=json.loads(compose(project,"config","--format","json"))
    if config["name"]!=project or set(config["volumes"])!={"postgres","rustfs","rabbitmq"}:
        raise ValueError("Unexpected project/volume signature")
    expected={project+"_"+name for name in config["volumes"]}
    volumes=json.loads(run(["docker","volume","inspect",*sorted(expected)]))
    for volume in volumes:
        if volume.get("Labels",{}).get("com.docker.compose.project")!=project:
            raise ValueError("Foreign volume owner")
    ids=run(["docker","ps","-aq"]).split()
    containers=json.loads(run(["docker","inspect",*ids])) if ids else []
    selected=[]
    for container in containers:
        labels=container["Config"].get("Labels",{})
        mounts={m.get("Name") for m in container.get("Mounts",[]) if m["Type"]=="volume"}
        if mounts & expected and labels.get("com.docker.compose.project")!=project:
            raise ValueError("Volume shared with another project")
        if labels.get("com.docker.compose.project")==project and labels.get("com.docker.compose.oneoff","").lower()!="true":
            validate_labels(labels)
            if Path(labels.get("com.docker.compose.project.config_files","")).resolve()!=SCOPES[project].resolve():
                raise ValueError("Container belongs to a different Compose definition")
            environment_values=dict(item.split("=",1) for item in container["Config"].get("Env",[]) if "=" in item)
            if "DB_HOST" in environment_values and environment_values["DB_HOST"]!="postgres":
                raise ValueError("External database endpoint rejected")
            if "MLFLOW_S3_ENDPOINT_URL" in environment_values and environment_values["MLFLOW_S3_ENDPOINT_URL"]!="http://rustfs:9000":
                raise ValueError("External object store rejected")
            selected.append({"id":container["Id"],"service":labels.get("com.docker.compose.service"),"image":container["Image"]})
    if not {"postgres","rustfs","mlflow"}<={c["service"] for c in selected}:
        raise ValueError("Missing dedicated services; cannot verify ownership")
    return {"project":project,"directory":str(ROOT),"compose_sha256":hashlib.sha256(SCOPES[project].read_bytes()).hexdigest(),
            "volumes":sorted(expected),"containers":sorted(selected,key=lambda c:c["service"])}


def validate_labels(labels):
    if labels.get("io.marista.environment")!="poc" or labels.get("io.marista.solution")!="horarios-inteligentes":
        raise ValueError("Actual container environment/solution is not the authorized POC")


def data_inventory(project):
    output=compose(project,"run","--rm","--no-deps","-T","--entrypoint","python",
                   "-v",str(ROOT/"src")+":/app/src:ro","tools","-m","src.persistence.reset_inventory")
    return json.loads(output)


def preview(environment,project,mode):
    scope=validate_scope(environment,project)
    inventory=data_inventory(project)
    if inventory["database_names"]!=["mlflow_db","planejamento_db","postgres"] or inventory["buckets"]!=["pucpr-poc"]:
        raise ValueError("Unexpected database or bucket: shared-resource scope rejected")
    plan=dict(plan_id=str(uuid.uuid4()),created_at_utc=datetime.now(timezone.utc).isoformat(),environment=environment,
              mode=mode,scope=scope,inventory=inventory,preserved=preserved(),status="PREVIEW")
    plan["plan_hash"]=digest(plan)
    REPORTS.mkdir(parents=True,exist_ok=True)
    (REPORTS/(plan["plan_id"]+".plan.json")).write_text(json.dumps(plan,indent=2),encoding="utf-8")
    return plan


def validate_plan(plan,phrase,execute,environment,project):
    if not execute or phrase!=PHRASE:
        raise ValueError("Explicit --execute and exact typed confirmation are required")
    if environment!="poc" or project not in SCOPES or plan["environment"]!=environment or plan["scope"]["project"]!=project:
        raise ValueError("Scope mismatch")
    original={k:v for k,v in plan.items() if k!="plan_hash"}
    if plan["plan_hash"]!=digest(original):
        raise ValueError("Modified plan")
    if datetime.now(timezone.utc)-datetime.fromisoformat(plan["created_at_utc"])>timedelta(minutes=15):
        raise ValueError("Expired plan; preview again")
    if plan["scope"]!=validate_scope(environment,project) or plan["inventory"]!=data_inventory(project):
        raise ValueError("Stale inventory; preview again")
    if plan["preserved"]!=preserved():
        raise ValueError("Protected files changed; preview again")


@contextmanager
def lock():
    REPORTS.mkdir(parents=True,exist_ok=True)
    path=REPORTS/"controller.lock"
    descriptor=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(descriptor,str(os.getpid()).encode())
        yield
    finally:
        os.close(descriptor)
        path.unlink()


def execute_plan(plan,environment,project,phrase,execute,reinitialize):
    validate_plan(plan,phrase,execute,environment,project)
    if plan["mode"]=="factory-reset" and any(o["key"].startswith("backups/") for o in plan["inventory"]["objects"]):
        raise ValueError("Backups inside volume: export and verify externally before reset")
    result=dict(plan_id=plan["plan_id"],status="RESET_FAILED",steps=[],timestamp_utc=datetime.now(timezone.utc).isoformat())
    with lock():
        try:
            validate_plan(plan,phrase,execute,environment,project)
            compose(project,"stop")
            result["steps"].append("writers stopped")
            compose(project,"up","-d","--wait","--wait-timeout","180","postgres","rustfs","rabbitmq")
            if plan["inventory"]!=data_inventory(project):
                raise ValueError("Writes occurred during quiescence; preview again")
            # Ownership/foreign consumers were verified against actual Docker labels.
            # Only this explicit factory-reset path can remove named POC volumes.
            if plan["mode"]=="factory-reset":
                compose(project,"down","--volumes")
                result["steps"].append("exclusive volumes removed")
            else:
                compose(project,"up","-d","--wait","--wait-timeout","180","postgres","rustfs","rabbitmq")
                if plan["inventory"]!=data_inventory(project):
                    raise ValueError("Writes occurred during quiescence; preview again")
                compose(project,"run","--rm","--no-deps","-T","--entrypoint","python",
                        "-v",str(ROOT/"src")+":/app/src:ro","-e","POC_RESET_PLAN_ID="+plan["plan_id"],
                        "tools","-m","src.persistence.reset_data")
                result["steps"].append("scoped data removed, volumes preserved")
            if reinitialize:
                compose(project,"run","--rm","--no-deps","--entrypoint","chown","volume-tools","10001:10001","/restore/rustfs")
                compose(project,"up","-d","--wait","--wait-timeout","180","postgres","rustfs","rabbitmq")
                for command in ("bootstrap","migrate","buckets","migrate-mlflow"):
                    compose(project,"run","--rm","--no-deps","tools",command)
                if reinitialize=="demo-ready":
                    compose(project,"run","--rm","--no-deps","tools","seed")
                compose(project,"up","-d","--wait","--wait-timeout","300")
                after=data_inventory(project)
                for table in ("proposal_generations","proposal_lines","training_executions","prediction_jobs","model_deployments"):
                    if after["databases"]["planejamento_db"][table]["count"]:
                        raise ValueError("Unexpected business residue")
                for table in ("runs","registered_models","model_versions","trace_info"):
                    if after["databases"]["mlflow_db"].get(table,{}).get("count",0):
                        raise ValueError("Unexpected MLflow residue")
                if any(o["key"].startswith(("mlflow/","lineage/")) for o in after["objects"]):
                    raise ValueError("Unexpected Object Store residue")
                if any(q["messages"] for q in after["queues"]):
                    raise ValueError("Unexpected queue residue")
                result["after"]=after
            if preserved()!=plan["preserved"]:
                raise ValueError("Protected file integrity mismatch")
            result["status"]="RESET_PASS"
        except Exception as error:
            result.update(status="RESET_PARTIAL" if result["steps"] else "RESET_FAILED",error_type=type(error).__name__)
            raise
        finally:
            (REPORTS/(plan["plan_id"]+".result.json")).write_text(json.dumps(result,indent=2),encoding="utf-8")
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["preview","execute","status"])
    parser.add_argument("--environment",required=True)
    parser.add_argument("--project",required=True)
    parser.add_argument("--mode",choices=["factory-reset","reset-data"],default="factory-reset")
    parser.add_argument("--plan-id")
    parser.add_argument("--execute",action="store_true")
    parser.add_argument("--confirmation")
    parser.add_argument("--reinitialize",choices=["empty","demo-ready"])
    args=parser.parse_args()
    if args.action=="preview":
        print(json.dumps(preview(args.environment,args.project,args.mode),indent=2))
    else:
        identifier=str(uuid.UUID(args.plan_id))
        suffix=".result.json" if args.action=="status" else ".plan.json"
        plan=json.loads((REPORTS/(identifier+suffix)).read_text())
        if args.action=="status":
            print(json.dumps(plan,indent=2))
        else:
            phrase=args.confirmation or input("Digite a frase de confirmação: ")
            print(json.dumps(execute_plan(plan,args.environment,args.project,phrase,args.execute,args.reinitialize),indent=2))


if __name__=="__main__":
    main()
