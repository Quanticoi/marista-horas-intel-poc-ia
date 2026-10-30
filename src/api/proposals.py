from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from src.persistence.db import rows


def router(auth):
    routes = APIRouter(prefix="/v1/proposals", dependencies=[Depends(auth)])

    @routes.get("")
    def list_proposals(cycle: str, course_id: UUID | None = None,
                       limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
        return rows("""SELECT g.execution_id,g.cycle_id,g.run_id,g.model_name,g.model_version,g.status,l.*
            FROM planning.proposal_generations g JOIN planning.academic_cycles c ON c.id=g.cycle_id
            JOIN planning.proposal_lines l USING(execution_id)
            WHERE c.cycle_code=:cycle AND (CAST(:course AS uuid) IS NULL OR l.course_id=:course)
            ORDER BY g.generated_at DESC,g.execution_id,l.course_id,l.period_id,l.discipline_id
            LIMIT :limit OFFSET :offset""",dict(cycle=cycle,course=course_id,limit=limit,offset=offset))

    @routes.get("/{execution_id}")
    def generation(execution_id: UUID):
        found = rows("SELECT * FROM planning.proposal_generations WHERE execution_id=:id", {"id":execution_id})
        if not found:
            raise HTTPException(404,"Proposal generation not found")
        return found[0]

    @routes.get("/{execution_id}/lines")
    def lines(execution_id: UUID, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0)):
        generation(execution_id)
        return rows("""SELECT * FROM planning.proposal_lines WHERE execution_id=:id
            ORDER BY course_id,period_id,discipline_id LIMIT :limit OFFSET :offset""",
            dict(id=execution_id,limit=limit,offset=offset))
    return routes
