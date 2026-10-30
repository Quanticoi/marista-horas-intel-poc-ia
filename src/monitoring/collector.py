"""Best-effort log collector: bounded reads, PVC checkpoints and rotation."""
import hashlib
import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from kubernetes import client, config as kube_config
from src.common.settings import config
from src.common.logging import redact, event

DIRECTORY = Path(os.getenv("LOG_DIRECTORY", "/logs"))
NAMESPACES = ("training","mlops","ai-service","data","operations")


def kube():
    kube_config.load_incluster_config()
    return client.CoreV1Api()


def collect_once(api, checkpoint):
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    cfg = config("logging")
    active = DIRECTORY/"current.jsonl"
    if active.exists() and active.stat().st_size >= cfg["rotate_bytes"]:
        active.rename(DIRECTORY/f"{time.time_ns()}.jsonl")
    for namespace in NAMESPACES:
        for pod in api.list_namespaced_pod(namespace, _request_timeout=5).items:
            for container in pod.spec.containers:
                key = f"{pod.metadata.uid}/{container.name}"
                try:
                    previous = checkpoint.get(key,{})
                    args = {"since_time":previous["timestamp"]} if previous.get("timestamp") else {"since_seconds":300}
                    raw = api.read_namespaced_pod_log(pod.metadata.name, namespace, container=container.name,
                        timestamps=True, limit_bytes=262144, _request_timeout=5, **args)
                    hashes = set(previous.get("hashes",[]))
                    last_time = previous.get("timestamp")
                    with active.open("a",encoding="utf-8") as stream:
                        for line in raw.splitlines():
                            timestamp, _, message = line.partition(" ")
                            digest = hashlib.sha256(line.encode()).hexdigest()
                            if timestamp == last_time and digest in hashes:
                                continue
                            try:
                                fields = json.loads(message)
                                if not isinstance(fields,dict):
                                    fields = {"message":message}
                            except ValueError:
                                fields = {"message":message}
                            fields.update(timestamp=timestamp,namespace=namespace,pod=pod.metadata.name,
                                service=pod.metadata.labels.get("app",container.name))
                            fields.setdefault("level","INFO")
                            stream.write(json.dumps(redact(fields),default=str)+"\n")
                            if timestamp != last_time:
                                hashes = set()
                            last_time = timestamp
                            hashes.add(digest)
                    checkpoint[key] = dict(timestamp=last_time,hashes=list(hashes)[-1000:])
                except Exception as error:
                    event("collector","collection failed",level="WARNING",error=type(error).__name__,pod=pod.metadata.name)
    alive = {str(p.metadata.uid) for ns in NAMESPACES for p in api.list_namespaced_pod(ns,_request_timeout=5).items}
    checkpoint = {key:value for key,value in checkpoint.items() if key.split("/")[0] in alive}
    temporary = DIRECTORY/"checkpoint.tmp"
    temporary.write_text(json.dumps(checkpoint),encoding="utf-8")
    temporary.replace(DIRECTORY/"checkpoint.json")
    files = sorted(DIRECTORY.glob("*.jsonl"), key=lambda p:p.stat().st_mtime)
    size = sum(p.stat().st_size for p in files)
    for path in files:
        if path != active and (time.time()-path.stat().st_mtime > cfg["retention_days"]*86400 or size > cfg["max_bytes"]):
            size -= path.stat().st_size
            path.unlink()
    return checkpoint


def main():
    api = kube()
    path = DIRECTORY/"checkpoint.json"
    checkpoint = json.loads(path.read_text()) if path.exists() else {}
    while True:
        try:
            checkpoint = collect_once(api,checkpoint)
        except Exception as error:
            event("collector","poll failed",level="ERROR",error=type(error).__name__)
        time.sleep(config("logging")["poll_seconds"])


if __name__ == "__main__":
    main()
