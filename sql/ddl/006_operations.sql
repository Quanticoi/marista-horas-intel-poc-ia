-- Durable orchestration. MLflow schemas remain owned exclusively by MLflow.
CREATE TABLE planning.training_campaigns (
 campaign_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 idempotency_key text UNIQUE NOT NULL, request_hash char(64) NOT NULL,
 request jsonb NOT NULL, correlation_id text NOT NULL, requested_by text NOT NULL,
 status text NOT NULL DEFAULT 'CREATED' CHECK(status IN
 ('CREATED','RUNNING','PAUSING','PAUSED','CANCELLING','CANCELLED','PARTIAL','COMPLETED','FAILED')),
 max_parallel_jobs integer NOT NULL CHECK(max_parallel_jobs BETWEEN 1 AND 2),
 requested_count integer NOT NULL CHECK(requested_count BETWEEN 1 AND 600),
 created_at_utc timestamptz NOT NULL DEFAULT now(), started_at_utc timestamptz, ended_at_utc timestamptz
);
CREATE TABLE planning.operation_jobs (
 job_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), kind text NOT NULL CHECK(kind IN ('generation','training')),
 campaign_id uuid REFERENCES planning.training_campaigns, model_key text,
 idempotency_key text NOT NULL, request_hash char(64) NOT NULL, request jsonb NOT NULL,
 correlation_id text NOT NULL, requested_by text NOT NULL,
 status text NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','RUNNING','COMPLETED','FAILED','CANCELLED')),
 attempt integer NOT NULL DEFAULT 0, max_attempts integer NOT NULL DEFAULT 3 CHECK(max_attempts BETWEEN 1 AND 4),
 available_at_utc timestamptz NOT NULL DEFAULT now(), heartbeat_at_utc timestamptz,
 started_at_utc timestamptz, ended_at_utc timestamptz, created_at_utc timestamptz NOT NULL DEFAULT now(),
 result jsonb NOT NULL DEFAULT '{}', error_code text,
 UNIQUE(kind,idempotency_key), UNIQUE(campaign_id,model_key)
);
CREATE INDEX ix_operations_pending ON planning.operation_jobs(status,available_at_utc);
CREATE INDEX ix_operations_campaign ON planning.operation_jobs(campaign_id,status);
CREATE TABLE planning.operation_events (
 event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, job_id uuid REFERENCES planning.operation_jobs,
 campaign_id uuid REFERENCES planning.training_campaigns, event_type text NOT NULL,
 details jsonb NOT NULL DEFAULT '{}', created_at_utc timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_operation_event_immutable BEFORE UPDATE OR DELETE ON planning.operation_events
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE VIEW planning.training_campaign_items AS
 SELECT job_id,campaign_id,model_key,status,attempt,heartbeat_at_utc,started_at_utc,ended_at_utc,
 result->>'run_id' AS mlflow_run_id,result->>'model_name' AS registered_model_name,
 result->>'model_version' AS model_version,error_code,result
 FROM planning.operation_jobs WHERE kind='training';
CREATE TABLE planning.model_approval_requests (
 approval_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), model_name text NOT NULL, model_version text NOT NULL,
 action text NOT NULL CHECK(action IN ('APPROVE','REVOKE','ROLLBACK')), reason text NOT NULL,
 requested_by text NOT NULL, reviewed_by text, correlation_id text NOT NULL,
 status text NOT NULL DEFAULT 'REQUESTED' CHECK(status IN ('REQUESTED','APPROVED','REJECTED','REVOKED','FAILED')),
 prior_version text, artifact_sha256 char(64), run_id text,
 created_at_utc timestamptz NOT NULL DEFAULT now(), reviewed_at_utc timestamptz
);
CREATE UNIQUE INDEX ix_model_current_approval ON planning.model_approval_requests(model_name)
 WHERE status='APPROVED';
