-- Read-only, planejamento_db. Bind parameters through SQLAlchemy text(); never interpolate.
-- :model_key text, :version text, :run_id text, :snapshot_id UUID,
-- :campaign_id UUID, :proposal_id UUID, :limit integer <=500, :offset integer >=0.
SELECT * FROM planning.v_model_inventory
 WHERE model_key=:model_key AND model_version=:version;

SELECT * FROM planning.v_training_inventory WHERE run_id=:run_id
 ORDER BY started_at_utc,job_id LIMIT :limit OFFSET :offset;

SELECT * FROM planning.v_model_inventory WHERE snapshot_id=:snapshot_id
 ORDER BY model_key,model_version::integer LIMIT :limit OFFSET :offset;

SELECT * FROM planning.v_training_inventory WHERE campaign_id=:campaign_id
 ORDER BY model_key,job_id LIMIT :limit OFFSET :offset;

SELECT * FROM planning.v_proposal_lineage_readable WHERE proposal_id=:proposal_id
 ORDER BY course_id,period_id,discipline_id LIMIT :limit OFFSET :offset;

SELECT * FROM planning.proposal_model_usage WHERE proposal_id=:proposal_id
 ORDER BY model_key,model_version;

SELECT * FROM planning.v_storage_manifest_inventory
 WHERE model_key=:model_key AND model_version=:version;

SELECT g.execution_id,g.row_count,count(l.*) AS stored_rows
 FROM planning.proposal_generations g JOIN planning.proposal_lines l USING(execution_id)
 WHERE g.execution_id=:proposal_id GROUP BY g.execution_id;
