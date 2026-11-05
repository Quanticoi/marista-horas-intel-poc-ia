import pytest
from src.persistence.reset_policy import SOURCE_TABLES,partition_tables


def test_source_is_not_in_truncation_set():
    source,derived=partition_tables(SOURCE_TABLES|{'workbench_campaigns','ai_proposals_v2','operation_jobs'})
    assert set(source)==SOURCE_TABLES
    assert derived==['ai_proposals_v2','operation_jobs','workbench_campaigns']
    assert not set(source)&set(derived)


def test_incomplete_source_schema_refuses_reset():
    with pytest.raises(ValueError,match='source schema incomplete'):
        partition_tables({'workbench_campaigns'})
