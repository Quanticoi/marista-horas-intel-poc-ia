-- SOURCE_DATABASE_URL, explicit immutable snapshot; same query used by academic_data.load.
SELECT payload FROM planning.model_training_observations
WHERE snapshot_id=:id ORDER BY offer_id,cycle_code;
