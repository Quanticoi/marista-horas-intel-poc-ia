CREATE TABLE planning.academic_simulation_snapshots (
 snapshot_id uuid PRIMARY KEY,dataset_sha256 text NOT NULL UNIQUE CHECK (dataset_sha256 ~ '^[0-9a-f]{64}$'),
 cycle_code text NOT NULL,seed integer NOT NULL,scenario_id text NOT NULL,
 manifest jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE planning.model_training_observations (
 snapshot_id uuid NOT NULL REFERENCES planning.academic_simulation_snapshots(snapshot_id),
 offer_id uuid NOT NULL,cycle_code text NOT NULL,cohort_id uuid NOT NULL,
 regular integer NOT NULL CHECK(regular>=0),dependency integer NOT NULL CHECK(dependency>=0),
 elective integer NOT NULL CHECK(elective>=0),split text NOT NULL CHECK(split IN ('HISTORY','FUTURE')),
 data_class text NOT NULL CHECK(data_class='SYNTHETIC_HISTORY'),payload jsonb NOT NULL,
 PRIMARY KEY(snapshot_id,offer_id,cycle_code)
);
CREATE VIEW planning.cohort_regular_demand AS
 SELECT snapshot_id,cohort_id,cycle_code,min(regular) AS regular,max(regular)=min(regular) AS consistent,
 'SYNTHETIC_HISTORY'::text AS data_class FROM planning.model_training_observations
 GROUP BY snapshot_id,cohort_id,cycle_code;
CREATE VIEW planning.discipline_nonregular_demand AS
 SELECT snapshot_id,offer_id,cycle_code,dependency,elective,data_class FROM planning.model_training_observations;
CREATE VIEW planning.discipline_total_demand AS
 SELECT snapshot_id,offer_id,cycle_code,regular,dependency,elective,regular+dependency+elective AS total,data_class
 FROM planning.model_training_observations;
GRANT SELECT,INSERT ON planning.academic_simulation_snapshots,planning.model_training_observations TO planning_app;
GRANT SELECT ON planning.academic_simulation_snapshots,planning.model_training_observations,
 planning.cohort_regular_demand,planning.discipline_nonregular_demand,planning.discipline_total_demand TO planning_readonly;
GRANT SELECT ON planning.cohort_regular_demand,planning.discipline_nonregular_demand,planning.discipline_total_demand TO planning_app;
