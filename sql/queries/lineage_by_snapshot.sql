SELECT * FROM planning.v_lineage_proposal WHERE snapshot_id=:snapshot_id
ORDER BY proposal_id, model_key LIMIT :limit OFFSET :offset;
