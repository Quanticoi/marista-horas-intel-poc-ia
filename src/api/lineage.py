"""Authenticated reverse lookup, without cross-database foreign keys."""
from fastapi import APIRouter,Depends,Query,HTTPException
from src.persistence.db import rows


def router(auth):
    routes=APIRouter(prefix="/v1/lineage",dependencies=[Depends(auth)])

    @routes.get("")
    def lookup(kind: str, external_id: str, limit: int=Query(100,ge=1,le=500), offset: int=Query(0,ge=0)):
        fields={"proposal":"proposal_id::text","run":"run_id","model":"model_key","snapshot":"snapshot_id::text"}
        if kind not in fields:
            raise HTTPException(422,"kind must be proposal, run, model or snapshot")
        found=rows("SELECT * FROM planning.v_lineage_proposal WHERE "+fields[kind]+"=:id ORDER BY proposal_id,model_key,model_version LIMIT :limit OFFSET :offset",
                   dict(id=external_id,limit=limit,offset=offset))
        return dict(kind=kind,external_id=external_id,status="FOUND" if found else "NOT_FOUND",items=found,limit=limit,offset=offset)
    return routes
