SELECT * FROM planning.v_lineage_proposal WHERE run_id=:run_id
ORDER BY proposal_id, model_key LIMIT :limit OFFSET :offset;
