"""HI-LINEAGE/1.0: typed public identities and canonical, secret-free manifests."""
import hashlib
import json
import re
from datetime import datetime, timezone
from uuid import UUID
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

SCHEMA = "HI-LINEAGE/1.0"
CONTRACT = "poc-planilha-turmas-v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False, default=str).encode("utf-8")


def sha256(value):
    return hashlib.sha256(value if isinstance(value, bytes) else canonical(value)).hexdigest()


class Identity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    solution_id: Literal["horarios-inteligentes"] = "horarios-inteligentes"
    environment: Literal["poc"] = "poc"
    domain: Literal["planilha-turmas"] = "planilha-turmas"
    academic_cycle_id: UUID
    snapshot_id: UUID
    snapshot_sha256: str = Field(pattern="^[a-f0-9]{64}$")
    dataset_sha256: str = Field(pattern="^[a-f0-9]{64}$")
    model_key: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,160}$")
    code_version: str = Field(pattern=r"^(sha256:)?[a-f0-9]{7,80}$")
    config_hash: str = Field(pattern="^[a-f0-9]{64}$")
    ruleset_version: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,160}$")
    ruleset_hash: str = Field(pattern="^[a-f0-9]{64}$")
    source_type: Literal["DEMO", "REAL"]
    training_campaign_id: UUID | None = None

    def tags(self):
        return {k: str(v) for k, v in self.model_dump(mode="json").items() if v is not None}


def reject_sensitive(value):
    """Reject credentials in manifests, including unknown nested fields."""
    if isinstance(value, dict):
        for key, item in value.items():
            if re.search(r"password|secret|token|authorization|database_url|access_key|credential|connection_string", str(key), re.I):
                raise ValueError("Sensitive metadata key rejected")
            reject_sensitive(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            reject_sensitive(item)
    elif isinstance(value, str) and re.search(r"://[^/\s]+@|Bearer\s|X-Amz-Signature=", value, re.I):
        raise ValueError("Sensitive metadata value rejected")


def manifest(kind, identity, created_at, **references):
    result = dict(manifest_schema_version=SCHEMA, entity_type=kind,
                  created_at_utc=created_at, **identity, **references)
    reject_sensitive(result)
    canonical(result)
    return result


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def put_manifest(key, document):
    """Conditional immutable write; identical retry succeeds, collision fails."""
    from src.data.storage import s3, bucket
    from botocore.exceptions import ClientError
    if not re.fullmatch(r"(?:lineage|snapshots)/[A-Za-z0-9_./-]+/manifest.json", key) or ".." in key:
        raise ValueError("Invalid manifest key")
    reject_sensitive(document)
    body = canonical(document)
    client = s3()
    try:
        client.put_object(Bucket=bucket(), Key=key, Body=body,
                          ContentType="application/json", IfNoneMatch="*")
    except ClientError as error:
        if error.response["ResponseMetadata"]["HTTPStatusCode"] != 412:
            raise
        response = client.get_object(Bucket=bucket(), Key=key)
        try:
            existing = response["Body"].read()
        finally:
            response["Body"].close()
        if existing != body:
            raise ValueError("Immutable manifest collision") from None
    return {"uri": f"s3://{bucket()}/{key}", "sha256": sha256(body)}
