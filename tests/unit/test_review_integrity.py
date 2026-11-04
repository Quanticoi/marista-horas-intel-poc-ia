"""Regression checks for review synchronization, cache inventory and lineage claims."""
from types import SimpleNamespace
import pytest
from src.operations.governance import synchronize_alias,alias_version
from src.persistence.lineage import provenance_label


class Registry:
    def __init__(self,version=None):
        self.version=version
        self.calls=[]
    def get_model_version_by_alias(self,name,alias):
        if self.version is None:
            from mlflow.exceptions import MlflowException
            raise MlflowException('missing',error_code='RESOURCE_DOES_NOT_EXIST')
        return SimpleNamespace(version=self.version)
    def set_registered_model_alias(self,name,alias,version):
        self.calls.append(('set',name,str(version)))
        self.version=str(version)
    def delete_registered_model_alias(self,name,alias):
        self.calls.append(('delete',name))
        self.version=None


def test_review_sync_changes_only_expected_alias():
    registry=Registry('2')
    synchronize_alias(registry,'hi.demo.test','APPROVE','3','2')
    assert registry.version=='3'
    synchronize_alias(registry,'hi.demo.test','APPROVE','3','2')
    assert registry.calls==[('set','hi.demo.test','3')]


def test_review_sync_refuses_unexpected_alias():
    from src.operations.jobs import Conflict
    registry=Registry('4')
    with pytest.raises(Conflict,match='differs'):
        synchronize_alias(registry,'hi.demo.test','APPROVE','3','2')
    assert registry.calls==[]


def test_review_sync_revocation_is_idempotent():
    registry=Registry('2')
    synchronize_alias(registry,'hi.demo.test','REVOKE','2','2')
    synchronize_alias(registry,'hi.demo.test','REVOKE','2','2')
    assert registry.calls==[('delete','hi.demo.test')]
    assert alias_version(registry,'hi.demo.test') is None


def test_lineage_record_is_not_runtime_verified():
    assert provenance_label({'inference_id':'abc','artifact_sha256':'a'*64})=='RECORDED'
    assert provenance_label({'inference_id':None,'artifact_sha256':'a'*64})=='LEGACY_PARTIAL'
