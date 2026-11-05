-- Protect source and synthetic provenance even if role defaults grant UPDATE/DELETE.
CREATE TRIGGER academic_source_immutable BEFORE UPDATE OR DELETE ON planning.academic_source_files
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE TRIGGER academic_reference_immutable BEFORE UPDATE OR DELETE ON planning.academic_reference_rows
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE TRIGGER academic_dictionary_immutable BEFORE UPDATE OR DELETE ON planning.academic_data_dictionary
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE TRIGGER academic_simulation_immutable BEFORE UPDATE OR DELETE ON planning.academic_simulation_snapshots
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE TRIGGER academic_observations_immutable BEFORE UPDATE OR DELETE ON planning.model_training_observations
 FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
