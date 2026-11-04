"""Monitoring never trains or promotes. Actuals must exist in a later sealed snapshot."""
import uuid
from sqlalchemy import text
from src.persistence.db import engine, rows


def evaluate(cycle_id):
    # No fabricated actuals: use the most recent sealed history for exactly the target period.
    query="""SELECT p.*,h.actual_students FROM planning.predictions p
      JOIN planning.academic_cycles c ON c.id=p.cycle_id
      JOIN LATERAL (SELECT he.regular_students+he.dependency_students+he.elective_students AS actual_students
        FROM planning.historical_enrollments he JOIN planning.dataset_snapshots s ON s.id=he.snapshot_id
        WHERE he.campus_id=p.campus_id AND he.course_id=p.course_id AND he.period_id=p.period_id
          AND he.reference_year=c.target_year AND he.reference_semester=c.target_semester AND s.sealed_at IS NOT NULL
        ORDER BY s.as_of_date DESC,s.created_at DESC LIMIT 1) h ON true
      WHERE p.cycle_id=:cycle"""
    predictions=rows(query,{"cycle":cycle_id})
    if not predictions:
        return {"status":"PENDING_ACTUALS","evaluations":0}
    with engine().begin() as con:
        for prediction in predictions:
            error=abs(prediction["actual_students"]-prediction["forecast_students"])
            status="REVIEW" if error>max(10,prediction["actual_students"]*.2) else "OK"
            con.execute(text("""INSERT INTO planning.model_quality_evaluations
                (id,model_id,deployment_id,cycle_id,actual_students,predicted_students,absolute_error,quality_status)
                VALUES (:id,:model,:deployment,:cycle,:actual,:predicted,:error,:status)"""),
                dict(id=uuid.uuid4(),model=prediction["model_id"],deployment=prediction["deployment_id"],cycle=cycle_id,
                     actual=prediction["actual_students"],predicted=prediction["forecast_students"],error=error,status=status))
    return {"status":"EVALUATED","evaluations":len(predictions)}


def monitor():
    return rows("SELECT model_id,quality_status,max(evaluated_at) AS last_evaluation FROM planning.model_quality_evaluations GROUP BY model_id,quality_status",role="readonly")
