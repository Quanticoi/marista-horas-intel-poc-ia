from functools import lru_cache
from sqlalchemy import create_engine, text
from src.common.settings import database_url
from src.common.tracing import operation_span


@lru_cache
def engine(role="app"):
    return create_engine(database_url(role), pool_pre_ping=True, pool_size=5,
                         max_overflow=5, connect_args={"connect_timeout": 5})


def rows(sql, params=None, role="app"):
    with operation_span("postgres.query", database="planejamento_db", schema="planning"), engine(role).connect() as con:
        return [dict(r) for r in con.execute(text(sql), params or {}).mappings()]


def audit(con, actor, kind, entity, entity_id, correlation, new=None, reason=None):
    import json
    con.execute(text("""INSERT INTO planning.audit_events
      (actor_type,actor_id,event_type,entity_type,entity_id,correlation_id,new_value,reason)
      VALUES ('OPERATOR',:actor,:kind,:entity,:id,:correlation,CAST(:new AS jsonb),:reason)"""),
      dict(actor=actor, kind=kind, entity=entity, id=str(entity_id), correlation=correlation,
           new=json.dumps(new, default=str), reason=reason))
