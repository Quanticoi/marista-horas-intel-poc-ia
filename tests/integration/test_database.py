import uuid
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from src.persistence.db import engine,rows,audit

pytestmark=pytest.mark.integration


def test_database_roles_are_separate_and_app_cannot_ddl_or_truncate():
    result=rows("""SELECT current_database() AS db,current_user AS role,
      has_schema_privilege(current_user,'planning','CREATE') AS ddl,
      has_table_privilege(current_user,'planning.audit_events','TRUNCATE') AS truncate""")[0]
    assert result=={'db':'planejamento_db','role':'planning_app','ddl':False,'truncate':False}
    assert rows('SELECT current_database() AS db',role='mlflow')[0]['db']=='mlflow_db'


def test_audit_append_only():
    with engine().connect() as con:
        transaction=con.begin()
        try:
            audit(con,'test','TEST','test',uuid.uuid4(),'integration-test')
            savepoint=con.begin_nested()
            try:
                with pytest.raises(DBAPIError):
                    con.execute(text("UPDATE planning.audit_events SET reason='forbidden' WHERE correlation_id='integration-test'"))
            finally:
                savepoint.rollback()
        finally:
            transaction.rollback()


def test_snapshot_checksum_and_seal():
    from src.data.pipeline import load
    snapshots=rows("SELECT id FROM planning.dataset_snapshots WHERE sealed_at IS NOT NULL ORDER BY created_at DESC LIMIT 1")
    assert snapshots,'Execute seed antes do e2e'
    assert load(snapshots[0]['id']).model_key.nunique()==30
    with engine().connect() as con:
        transaction=con.begin()
        try:
            with pytest.raises(DBAPIError):
                con.execute(text("UPDATE planning.dataset_snapshots SET row_count=0 WHERE id=:id"),{'id':snapshots[0]['id']})
        finally:
            transaction.rollback()
