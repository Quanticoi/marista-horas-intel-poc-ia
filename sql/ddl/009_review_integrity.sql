-- Safe, additive state-machine and integrity semantics. Never modify MLflow-owned schemas.
ALTER TABLE planning.model_approval_requests
  DROP CONSTRAINT model_approval_requests_status_check;
ALTER TABLE planning.model_approval_requests
  ADD CONSTRAINT model_approval_requests_status_check
  CHECK (status IN ('REQUESTED','RECONCILING','APPROVED','REJECTED','REVOKED','FAILED'));

ALTER TABLE planning.proposal_model_usage
  DROP CONSTRAINT proposal_model_usage_provenance_status_check;
ALTER TABLE planning.proposal_model_usage
  ADD CONSTRAINT proposal_model_usage_provenance_status_check
  CHECK (provenance_status IN ('RECORDED','VERIFIED','LEGACY_PARTIAL'));

-- Historical VERIFIED values are immutable statements from earlier POC runs.
-- They remain unchanged; authoritative validation is GET /v1/audit/proposal/{id}.
CREATE INDEX IF NOT EXISTS ix_review_reconciling_model
  ON planning.model_approval_requests(model_name) WHERE status='RECONCILING';
