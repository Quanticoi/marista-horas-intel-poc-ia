SELECT * FROM planning.v_lineage_proposal WHERE model_key=:model_key
ORDER BY proposal_id, model_version LIMIT :limit OFFSET :offset;
