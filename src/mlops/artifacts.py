"""Verify every byte before loading a trusted, approved sklearn model bundle."""
import hashlib
import json
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse
import mlflow.sklearn
from src.data.storage import s3, bucket

MAX_FILE = 64 * 1024 * 1024
MAX_BUNDLE = 128 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def manifest(directory, provenance):
    files = {}
    for path in sorted(Path(directory).rglob("*")):
        if path.is_file():
            content = path.read_bytes()
            files[path.relative_to(directory).as_posix()] = {"sha256": digest(content), "size": len(content)}
    body = json.dumps({"schema_version": "2.0", **provenance, "files": files}, sort_keys=True).encode()
    (Path(directory) / "bundle.json").write_bytes(body)
    return digest(body)


def object_prefix(uri):
    if uri.startswith("mlflow-artifacts:/"):
        uri = f"s3://{bucket()}/mlflow/" + uri.removeprefix("mlflow-artifacts:/").lstrip("/")
    location = urlparse(uri)
    if location.scheme != "s3" or location.netloc != bucket() or not location.path.startswith("/mlflow/") or location.query or location.fragment:
        raise ValueError("Artifact outside approved object storage")
    if ".." in PurePosixPath(location.path).parts:
        raise ValueError("Invalid artifact path")
    return location.path.lstrip("/").rstrip("/")


def read(client, key, limit):
    response = client.get_object(Bucket=bucket(), Key=key)
    body = response["Body"]
    try:
        data = body.read(limit + 1)
    finally:
        body.close()
    if len(data) > limit:
        raise ValueError("Artifact too large")
    return data


def load_bundle(uri, expected_sha, deserialize=True):
    prefix, client = object_prefix(uri), s3()
    body = read(client, prefix + "/bundle.json", 1024 * 1024)
    if not expected_sha or digest(body) != expected_sha:
        raise ValueError("Bundle checksum mismatch")
    info = json.loads(body)
    files = info.get("files", {})
    if info.get("schema_version") != "2.0" or not {"MLmodel", "model.pkl"} <= files.keys() or len(files) > 100:
        raise ValueError("Unsupported model bundle; retrain legacy JSON models")
    total = 0
    with tempfile.TemporaryDirectory() as folder:
        for name, expected in files.items():
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
                raise ValueError("Unsafe bundle path")
            content = read(client, prefix + "/" + name, MAX_FILE)
            total += len(content)
            if total > MAX_BUNDLE or len(content) != expected["size"] or digest(content) != expected["sha256"]:
                raise ValueError("Artifact checksum or size mismatch")
            target = Path(folder) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        # Only load artifacts from the trusted training identity after approval/checksum checks.
        model = mlflow.sklearn.load_model(folder) if deserialize else None
    return model, info
