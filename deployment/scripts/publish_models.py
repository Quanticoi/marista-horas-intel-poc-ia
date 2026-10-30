"""Render dedicated model containers from audited approvals; no Docker socket in apps."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]


def render(model):
    name = "model-" + hashlib.sha256(model["model_key"].encode()).hexdigest()[:16]
    env = dict(DB_HOST="postgres", MLFLOW_TRACKING_URI="http://mlflow:5000",
        MLFLOW_S3_ENDPOINT_URL="http://rustfs:9000", S3_BUCKET="pucpr-poc",
        MODEL_KEY=model["model_key"], REGISTERED_VERSION=str(model["registered_version"]),
        MODEL_DEPLOYMENT_ID=str(model["deployment_id"]))
    for key in ("READONLY_PASSWORD", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "INFERENCE_TOKEN"):
        env[key] = "${" + key + ":?Configure .env}"
    return name, dict(image="marista-app:compose", restart="unless-stopped", mem_limit="512m",
        environment=env, ports=["127.0.0.1::8001"],
        command=["python", "-m", "uvicorn", "src.inference.model_api:app", "--host", "0.0.0.0", "--port", "8001"],
        depends_on={n:{"condition":"service_healthy"} for n in ("postgres", "rustfs", "mlflow")},
        healthcheck=dict(test=["CMD", "python", "-m", "src.common.service_check", "model"],
            interval="30s", timeout="30s", retries=3, start_period="120s"),
        logging=dict(driver="json-file", options={"max-size":"10m", "max-file":"3"}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="all")
    args = parser.parse_args()
    values = dict(line.split("=",1) for line in (ROOT / ".env").read_text(encoding="utf-8-sig").splitlines()
                  if line and not line.startswith("#") and "=" in line)
    req = Request("http://127.0.0.1:8000/v1/models", headers={"Authorization":"Bearer " + values["API_TOKEN"]})
    with urlopen(req, timeout=15) as response:
        models = json.load(response)
    approved = [m for m in models if m.get("deployment_id")]
    selected = [m for m in approved if args.model == "all" or m["model_key"] == args.model]
    if not selected:
        raise SystemExit("No approved model selected. Train and explicitly approve a binary version first.")
    path = ROOT / ".runtime/models.compose.json"
    old = json.loads(path.read_text()) if path.exists() else {"services":{}}
    # Remove obsolete desired entries; running revoked containers fail closed until explicitly stopped.
    active = {"model-" + hashlib.sha256(m["model_key"].encode()).hexdigest()[:16] for m in approved}
    services = {k:v for k,v in old["services"].items() if k in active}
    for model in selected:
        query = urlencode({"name":model["model_key"], "version":model["registered_version"]})
        with urlopen("http://127.0.0.1:5000/api/2.0/mlflow/model-versions/get?"+query, timeout=15) as response:
            version = json.load(response)["model_version"]
        tags = {t["key"]:t["value"] for t in version.get("tags",[])}
        if tags.get("schema_version") != "2.0" or len(tags.get("bundle_sha256", "")) != 64:
            raise SystemExit("Legacy/unverified version cannot be published; retrain using the C3 notebook.")
        name, service = render(model)
        services[name] = service
        print(f"{model['model_key']} version={model['registered_version']} service={name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({"services":services}, indent=2)+"\n", encoding="utf-8")
    temporary.replace(path)


if __name__ == "__main__":
    main()
