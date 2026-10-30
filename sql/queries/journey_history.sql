-- journey-history-v1. Target: total students per period, replicated to its disciplines
-- under the provisional POC rule: every discipline receives the whole cohort.
SELECT h.course_id::text, h.period_id::text, pd.discipline_id::text,
       h.reference_year * 2 + h.reference_semester - 1 AS semester_index,
       h.reference_semester AS semester,
       h.regular_students + h.dependency_students + h.elective_students AS students
FROM planning.historical_enrollments h
JOIN planning.dataset_snapshots s ON s.id = h.snapshot_id
JOIN planning.academic_cycles c ON c.id = s.cycle_id
JOIN planning.period_disciplines pd ON pd.period_id = h.period_id
WHERE h.snapshot_id = CAST(:snapshot AS uuid) AND c.cycle_code = :cycle
  AND s.sealed_at IS NOT NULL
  AND (CAST(:course AS text) IS NULL OR h.course_id::text = :course)
  AND h.reference_year * 2 + h.reference_semester - 1 < c.target_year * 2 + c.target_semester - 1
ORDER BY semester_index, h.course_id, h.period_id, pd.discipline_id
