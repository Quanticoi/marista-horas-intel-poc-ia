"""Authenticated reverse lookup, without cross-database foreign keys."""
from fastapi import APIRouter,Depends,Query,HTTPException
from src.persistence.db import rows


def router(auth):
    routes=APIRouter(prefix="/v1/lineage",dependencies=[Depends(auth)])

    @routes.get("/graph")
    def graph(kind:str,external_id:str,version:str="",limit:int=Query(100,ge=1,le=500),offset:int=Query(0,ge=0)):
        if kind not in ("proposal","run","model","snapshot","campaign"):
            raise HTTPException(422,"Invalid entity kind")
        identity=external_id+"/"+version if kind=="model" and version else external_id
        root=rows("SELECT entity_id FROM planning.lineage_entities WHERE entity_type=:kind AND external_id=:id",dict(kind=kind,id=identity))
        if not root:
            return dict(status="MISSING",nodes=[],edges=[],total_nodes=0,limit=limit,offset=offset)
        params=dict(root=root[0]["entity_id"],limit=limit,offset=offset)
        traversal="""WITH RECURSIVE connected(id) AS (
            SELECT CAST(:root AS uuid) UNION
            SELECT CASE WHEN e.parent_id=c.id THEN e.child_id ELSE e.parent_id END
            FROM planning.lineage_edges e JOIN connected c ON e.parent_id=c.id OR e.child_id=c.id)
            """
        nodes=rows(traversal+"SELECT e.* FROM planning.lineage_entities e JOIN connected c ON e.entity_id=c.id ORDER BY e.entity_type,e.external_id LIMIT :limit OFFSET :offset",params)
        count=rows(traversal+"SELECT count(*) AS total FROM connected",params)[0]["total"]
        edge_count=rows(traversal+"SELECT count(*) AS total FROM planning.lineage_edges WHERE parent_id IN (SELECT id FROM connected)",params)[0]["total"]
        edges=rows(traversal+"SELECT e.* FROM planning.lineage_edges e WHERE e.parent_id IN (SELECT id FROM connected) ORDER BY e.edge_id LIMIT :limit OFFSET :offset",params)
        return dict(status="VERIFIED" if max(count,edge_count)<=limit and offset==0 else "PARTIAL",nodes=nodes,edges=edges,total_nodes=count,total_edges=edge_count,limit=limit,offset=offset,
                    note="Graph existence only; verify artifact hashes separately. Edges have independent pagination.")

    @routes.get("")
    def lookup(kind: str, external_id: str, limit: int=Query(100,ge=1,le=500), offset: int=Query(0,ge=0)):
        fields={"proposal":"proposal_id::text","run":"run_id","model":"model_key","snapshot":"snapshot_id::text"}
        if kind=="campaign":
            found=rows("SELECT * FROM planning.training_campaign_items WHERE campaign_id::text=:id ORDER BY model_key LIMIT :limit OFFSET :offset",dict(id=external_id,limit=limit,offset=offset))
            return dict(kind=kind,external_id=external_id,status="FOUND" if found else "NOT_FOUND",items=found,limit=limit,offset=offset)
        if kind not in fields:
            raise HTTPException(422,"kind must be proposal, run, model or snapshot")
        found=rows("SELECT * FROM planning.v_lineage_proposal WHERE "+fields[kind]+"=:id ORDER BY proposal_id,model_key,model_version LIMIT :limit OFFSET :offset",
                   dict(id=external_id,limit=limit,offset=offset))
        return dict(kind=kind,external_id=external_id,status="FOUND" if found else "NOT_FOUND",items=found,limit=limit,offset=offset)
    return routes
