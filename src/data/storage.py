import os
import boto3
from botocore.config import Config
from src.common.settings import required


def s3():
    return boto3.client("s3", endpoint_url=required("MLFLOW_S3_ENDPOINT_URL"),
        aws_access_key_id=required("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=required("AWS_SECRET_ACCESS_KEY"),
        region_name="us-east-1", config=Config(signature_version="s3v4",
        connect_timeout=5, read_timeout=30, retries={"max_attempts": 3},
        s3={"addressing_style": "path"}))


def bucket():
    return os.getenv("S3_BUCKET", "pucpr-poc")


def artifact_destination():
    """Single server/proof mapping; MLflow proxy URI is relative to this destination."""
    return f's3://{bucket()}/mlflow'
