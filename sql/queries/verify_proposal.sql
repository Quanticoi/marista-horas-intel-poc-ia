-- Bind :execution_id; business database planejamento_db, schema planning.
SELECT g.execution_id, g.status, g.run_id, g.model_name, g.model_version,
       g.row_count, count(l.execution_id) AS stored_rows,
       sum(l.proposed_students) AS proposed_students,
       sum(l.proposed_groups) AS proposed_groups
FROM planning.proposal_generations g
JOIN planning.proposal_lines l USING (execution_id)
WHERE g.execution_id = :execution_id
GROUP BY g.execution_id;
