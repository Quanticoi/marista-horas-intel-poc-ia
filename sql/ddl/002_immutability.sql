CREATE OR REPLACE FUNCTION planning.protect_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.sealed_at IS NOT NULL THEN RAISE EXCEPTION 'sealed snapshot is immutable'; END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END; $$;
CREATE TRIGGER trg_snapshot_immutable BEFORE UPDATE OR DELETE ON planning.dataset_snapshots
FOR EACH ROW EXECUTE FUNCTION planning.protect_snapshot();

CREATE OR REPLACE FUNCTION planning.protect_history() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE sealed timestamptz;
BEGIN
  IF TG_OP IN ('UPDATE','DELETE') THEN
    IF EXISTS (SELECT 1 FROM planning.dataset_snapshots WHERE id=OLD.snapshot_id AND sealed_at IS NOT NULL) THEN
      RAISE EXCEPTION 'sealed history is immutable';
    END IF;
  END IF;
  IF TG_OP IN ('INSERT','UPDATE') THEN
    SELECT sealed_at INTO sealed FROM planning.dataset_snapshots WHERE id=NEW.snapshot_id FOR SHARE;
    IF sealed IS NOT NULL THEN RAISE EXCEPTION 'sealed history is immutable'; END IF;
    RETURN NEW;
  END IF;
  RETURN OLD;
END; $$;
CREATE TRIGGER trg_history_immutable BEFORE INSERT OR UPDATE OR DELETE ON planning.historical_enrollments
FOR EACH ROW EXECUTE FUNCTION planning.protect_history();

CREATE OR REPLACE FUNCTION planning.reject_prediction_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'original prediction/suggestion is immutable; record changes in audit'; END; $$;
CREATE TRIGGER trg_prediction_immutable BEFORE UPDATE OR DELETE ON planning.predictions
FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE TRIGGER trg_offer_immutable BEFORE UPDATE OR DELETE ON planning.offer_suggestions
FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
