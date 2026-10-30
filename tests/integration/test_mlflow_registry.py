"""Regression: PostgreSQL Registry must accept version IDs sent as strings."""
import uuid
import pytest
from mlflow import MlflowClient

pytestmark = pytest.mark.integration


def test_registry_get_model_version_accepts_string():
    client = MlflowClient()
    versions = list(client.search_model_versions(max_results=1))
    if versions:
        version = versions[0]
        actual = client.get_model_version(version.name, str(version.version))
        assert actual.name == version.name
        assert str(actual.version) == str(version.version)
        return
    # Empty CI database: create isolated metadata and remove it afterwards.
    name = 'registry-type-check-' + uuid.uuid4().hex
    client.create_registered_model(name)
    try:
        version = client.create_model_version(name, 's3://pucpr-poc/checks/compatibility')
        actual = client.get_model_version(name, str(version.version))
        assert actual.name == name
        assert str(actual.version) == str(version.version)
    finally:
        client.delete_registered_model(name)
