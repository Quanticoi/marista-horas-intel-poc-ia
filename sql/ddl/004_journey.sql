-- Draft proposals are separate from the approved operational prediction contract.
-- Existing catalog, snapshots, cycles and discipline keys are reused unchanged.
CREATE TABLE planning.proposal_generations (
    execution_id uuid PRIMARY KEY,
    correlation_id uuid NOT NULL,
    cycle_id uuid NOT NULL REFERENCES planning.academic_cycles(id),
    snapshot_id uuid NOT NULL REFERENCES planning.dataset_snapshots(id),
    course_scope text,
    dataset_sha256 char(64) NOT NULL,
    payload_sha256 char(64) NOT NULL,
    run_id text NOT NULL,
    experiment_id text NOT NULL,
    model_name text NOT NULL,
    model_version text NOT NULL,
    artifact_uri text NOT NULL,
    rule_version text NOT NULL,
    capacity integer NOT NULL CHECK (capacity > 0),
    mode text NOT NULL CHECK (mode = 'DEMO'),
    status text NOT NULL CHECK (status IN ('DRAFT','APPROVED','REJECTED')),
    row_count integer NOT NULL CHECK (row_count > 0),
    generated_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE planning.proposal_lines (
    execution_id uuid NOT NULL REFERENCES planning.proposal_generations(execution_id),
    course_id uuid NOT NULL REFERENCES planning.courses(id),
    period_id uuid NOT NULL REFERENCES planning.academic_periods(id),
    discipline_id uuid NOT NULL REFERENCES planning.disciplines(id),
    forecast_raw double precision NOT NULL,
    proposed_students integer NOT NULL CHECK (proposed_students >= 0),
    proposed_groups integer NOT NULL CHECK (proposed_groups >= 0),
    human_adjustment integer,
    PRIMARY KEY (execution_id, course_id, period_id, discipline_id)
);
CREATE INDEX ix_proposal_cycle ON planning.proposal_generations(cycle_id, generated_at);
CREATE TRIGGER trg_proposal_immutable BEFORE UPDATE OR DELETE ON planning.proposal_lines
FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
