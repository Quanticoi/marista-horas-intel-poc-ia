-- Additive presentation index. MLflow databases and pre-existing evidence are untouched.
CREATE TABLE planning.model_version_catalog (
 model_key text NOT NULL,model_version text NOT NULL CHECK(model_version ~ '^[1-9][0-9]*$'),
 run_id text NOT NULL,snapshot_id uuid NOT NULL REFERENCES planning.dataset_snapshots(id),
 campaign_id uuid REFERENCES planning.training_campaigns(campaign_id),metadata jsonb NOT NULL,
 manifest_uri text NOT NULL,manifest_sha256 char(64) NOT NULL,
 created_at_utc timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(model_key,model_version)
);
CREATE INDEX ix_catalog_run ON planning.model_version_catalog(run_id);
CREATE INDEX ix_catalog_snapshot ON planning.model_version_catalog(snapshot_id);
CREATE INDEX ix_catalog_campaign ON planning.model_version_catalog(campaign_id);
CREATE TRIGGER trg_catalog_immutable BEFORE UPDATE OR DELETE ON planning.model_version_catalog
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE VIEW planning.v_model_inventory AS
 SELECT model_key,model_version,run_id,snapshot_id,campaign_id,
 metadata->>'model_display_name' AS model_display_name,metadata->>'cycle_code' AS cycle_code,
 metadata->>'campus_code' AS campus_code,metadata->>'course_code' AS course_code,
 metadata->>'period_code' AS period_code,metadata->>'experiment_name' AS experiment_name,
 metadata->>'experiment_id' AS experiment_id,metadata->>'run_name' AS run_name,
 metadata->>'artifact_uri' AS artifact_uri,metadata->>'artifact_sha256' AS artifact_sha256,
 metadata->>'dataset_sha256' AS dataset_sha256,metadata->>'algorithm' AS algorithm,
 manifest_uri,manifest_sha256,'RECORDED'::text AS integrity_status,
 EXISTS(SELECT 1 FROM planning.model_approval_requests a WHERE a.model_name=c.model_key
   AND a.model_version=c.model_version AND a.status='APPROVED') AS sql_approved,
 metadata FROM planning.model_version_catalog c;
CREATE VIEW planning.v_training_inventory AS
 SELECT j.job_id,j.campaign_id,j.model_key,j.status,j.attempt,j.error_code,
 j.started_at_utc,j.ended_at_utc,j.correlation_id,
 c.request->>'campaign_display_name' AS campaign_display_name,
 j.result->>'run_id' AS run_id,j.result->>'model_version' AS model_version,
 j.result->'metrics' AS metrics,v.model_display_name,v.experiment_name,v.run_name,v.manifest_uri
 FROM planning.operation_jobs j LEFT JOIN planning.training_campaigns c USING(campaign_id)
 LEFT JOIN planning.v_model_inventory v ON v.model_key=j.model_key AND v.model_version=j.result->>'model_version'
 WHERE j.kind='training';
CREATE VIEW planning.v_storage_manifest_inventory AS
 SELECT model_key,model_version,run_id,manifest_uri,manifest_sha256,artifact_uri,artifact_sha256,
 metadata->'files' AS files FROM planning.v_model_inventory;
CREATE VIEW planning.v_proposal_lineage_readable AS
 SELECT g.execution_id AS proposal_id,'Planilha Turmas DEMO '||cy.cycle_code||' • '||g.status AS proposal_display_name,
 cy.cycle_code,g.snapshot_id,g.status,l.course_id,l.period_id,l.discipline_id,l.forecast_raw,
 l.proposed_students,l.proposed_groups,l.human_adjustment,
 COALESCE((SELECT jsonb_agg(jsonb_build_object('model_key',u.model_key,'model_display_name',v.model_display_name,
   'model_version',u.model_version,'run_id',u.run_id,'inference_id',u.inference_id,
   'manifest_uri',v.manifest_uri,'artifact_sha256',u.artifact_sha256,
   'evidence_state',CASE WHEN v.model_key IS NULL THEN 'LEGACY_PARTIAL' ELSE 'RECORDED' END))
   FROM planning.proposal_model_usage u LEFT JOIN planning.v_model_inventory v
   ON v.model_key=u.model_key AND v.model_version=u.model_version
   WHERE u.proposal_id=g.execution_id AND u.line_keys ? (l.course_id::text||'/'||l.period_id::text||'/'||l.discipline_id::text)),
   '[]'::jsonb) AS contributions
 FROM planning.proposal_generations g JOIN planning.academic_cycles cy ON cy.id=g.cycle_id
 JOIN planning.proposal_lines l ON l.execution_id=g.execution_id;
