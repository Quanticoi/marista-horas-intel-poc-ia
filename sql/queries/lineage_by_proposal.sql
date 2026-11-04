SELECT * FROM planning.v_lineage_proposal WHERE proposal_id=:proposal_id
ORDER BY model_key, model_version LIMIT :limit OFFSET :offset;
