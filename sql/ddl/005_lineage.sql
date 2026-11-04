-- Additive HI-LINEAGE/1.0. No MLflow-owned tables are touched.
CREATE TABLE planning.lineage_entities (
 entity_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 entity_type text NOT NULL, external_id text NOT NULL,
 environment text NOT NULL CHECK(environment='poc'), domain text NOT NULL,
 created_at_utc timestamptz NOT NULL DEFAULT now(), attributes jsonb NOT NULL,
 UNIQUE(entity_type,environment,external_id)
);
CREATE TABLE planning.lineage_edges (
 edge_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 parent_id uuid NOT NULL REFERENCES planning.lineage_entities,
 child_id uuid NOT NULL REFERENCES planning.lineage_entities,
 relation_type text NOT NULL CHECK(relation_type IN
 ('DERIVED_FROM','TRAINED_ON','REGISTERED_AS','PREDICTED_WITH','CONTRIBUTED_TO','EXPOSED_AS','REVISED_FROM')),
 created_at_utc timestamptz NOT NULL DEFAULT now(),
 UNIQUE(parent_id,child_id,relation_type)
);
CREATE INDEX ix_lineage_child ON planning.lineage_edges(child_id);
CREATE TABLE planning.proposal_model_usage (
 usage_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 proposal_id uuid NOT NULL REFERENCES planning.proposal_generations(execution_id),
 inference_id uuid,
 model_key text NOT NULL, registered_model_name text NOT NULL, model_version text NOT NULL,
 run_id text NOT NULL, snapshot_id uuid NOT NULL REFERENCES planning.dataset_snapshots(id),
 artifact_uri text NOT NULL, artifact_sha256 char(64), ruleset_hash char(64),
 line_keys jsonb, provenance_status text NOT NULL CHECK(provenance_status IN ('VERIFIED','LEGACY_PARTIAL')),
 created_at_utc timestamptz NOT NULL DEFAULT now(),
 UNIQUE(proposal_id,registered_model_name,model_version,run_id)
);
CREATE INDEX ix_usage_model ON planning.proposal_model_usage(model_key,model_version);
CREATE INDEX ix_usage_run ON planning.proposal_model_usage(run_id);
CREATE INDEX ix_usage_snapshot ON planning.proposal_model_usage(snapshot_id);
CREATE TABLE planning.proposal_contract_evidence (
 proposal_id uuid NOT NULL REFERENCES planning.proposal_generations(execution_id),
 proposal_revision integer NOT NULL CHECK(proposal_revision>0), schema_version text NOT NULL,
 payload_sha256 char(64) NOT NULL, published_at_utc timestamptz NOT NULL,
 row_count integer NOT NULL, validation_status text NOT NULL,
 validation_report_uri text, created_at_utc timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(proposal_id,proposal_revision,schema_version)
);
-- Old proposal metadata is factual; missing inference/hash/line attribution stay NULL.
INSERT INTO planning.proposal_model_usage
 (proposal_id,model_key,registered_model_name,model_version,run_id,snapshot_id,
 artifact_uri,provenance_status,created_at_utc)
SELECT execution_id,model_name,model_name,model_version,run_id,snapshot_id,artifact_uri,
 'LEGACY_PARTIAL',generated_at FROM planning.proposal_generations;
CREATE VIEW planning.v_lineage_proposal AS
 SELECT g.execution_id AS proposal_id,g.execution_id,g.cycle_id,g.snapshot_id,
 s.sha256 AS snapshot_sha256,g.dataset_sha256,g.generated_at,g.status,
 u.model_key,u.registered_model_name,u.model_version,u.run_id,u.inference_id,
 u.artifact_uri,u.artifact_sha256,u.ruleset_hash,u.provenance_status
 FROM planning.proposal_generations g JOIN planning.dataset_snapshots s ON s.id=g.snapshot_id
 JOIN planning.proposal_model_usage u ON u.proposal_id=g.execution_id;
CREATE TRIGGER trg_usage_immutable BEFORE UPDATE OR DELETE ON planning.proposal_model_usage
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE TRIGGER trg_contract_immutable BEFORE UPDATE OR DELETE ON planning.proposal_contract_evidence
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE TRIGGER trg_lineage_entity_immutable BEFORE UPDATE OR DELETE ON planning.lineage_entities
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE TRIGGER trg_lineage_edge_immutable BEFORE UPDATE OR DELETE ON planning.lineage_edges
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
