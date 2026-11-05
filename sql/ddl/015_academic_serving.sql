CREATE TABLE planning.academic_deployments (
 model_name text NOT NULL,model_version text NOT NULL,run_id text NOT NULL,snapshot_id uuid NOT NULL,
 request_key text NOT NULL UNIQUE,request_hash text NOT NULL,policy text NOT NULL CHECK(policy IN ('PRELOAD','LAZY')),
 status text NOT NULL CHECK(status IN ('DEPLOYED','UNAVAILABLE')),environment text NOT NULL CHECK(environment='poc'),
 metadata jsonb NOT NULL,expires_at timestamptz NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(model_name,model_version)
);
CREATE TABLE planning.ai_proposals_v2 (
 proposal_id uuid PRIMARY KEY REFERENCES planning.operation_jobs(job_id),snapshot_id uuid NOT NULL REFERENCES planning.academic_simulation_snapshots(snapshot_id),
 cycle_code text NOT NULL,revision integer NOT NULL DEFAULT 1,status text NOT NULL,
 header jsonb NOT NULL,payload_sha256 text NOT NULL,manifest_uri text,manifest_sha256 text,
 generated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE planning.ai_proposal_offers_v2 (
 proposal_id uuid NOT NULL REFERENCES planning.ai_proposals_v2(proposal_id),offer_id uuid NOT NULL,
 payload jsonb NOT NULL,PRIMARY KEY(proposal_id,offer_id)
);
CREATE TRIGGER academic_proposal_offer_immutable BEFORE UPDATE OR DELETE ON planning.ai_proposal_offers_v2
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE OR REPLACE FUNCTION planning.protect_academic_proposal_header() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 IF TG_OP='DELETE' OR OLD.header IS DISTINCT FROM NEW.header OR OLD.payload_sha256<>NEW.payload_sha256
 OR OLD.snapshot_id<>NEW.snapshot_id OR OLD.cycle_code<>NEW.cycle_code OR OLD.revision<>NEW.revision
 THEN RAISE EXCEPTION 'Original academic proposal is immutable'; END IF;
 RETURN NEW;
END; $$;
CREATE TRIGGER academic_proposal_header_immutable BEFORE UPDATE OR DELETE ON planning.ai_proposals_v2
 FOR EACH ROW EXECUTE FUNCTION planning.protect_academic_proposal_header();
GRANT SELECT,INSERT,UPDATE ON planning.academic_deployments,planning.ai_proposals_v2 TO planning_app;
GRANT SELECT,INSERT ON planning.ai_proposal_offers_v2 TO planning_app;
GRANT SELECT ON planning.academic_deployments,planning.ai_proposals_v2,planning.ai_proposal_offers_v2 TO planning_readonly;
