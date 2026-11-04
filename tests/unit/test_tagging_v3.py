from types import SimpleNamespace as N
import pytest
from src.common.tagging import component,functional_key,assert_shared,SCHEMA


def test_naming_is_functional_and_rejects_lossy_codes():
    assert functional_key('demo-c1','demo-cr1','p1')=='hi.pt.demanda.DEMO-C1.DEMO-CR1.P1'
    assert component('Ｐ１')=='P1'
    with pytest.raises(ValueError):
        component('Engenharia / Software')
    with pytest.raises(ValueError):
        component('Á')


def test_legacy_not_upgraded_by_presence():
    assert assert_shared(N(data=N(tags={})),N(tags={}))=='LEGACY_PARTIAL'


def test_conflicting_shared_tags_fail_closed():
    with pytest.raises(ValueError,match='MISMATCH'):
        assert_shared(N(data=N(tags={'lineage_schema_version':SCHEMA,'snapshot_id':'a'})),
                      N(tags={'lineage_schema_version':SCHEMA,'snapshot_id':'b'}))
