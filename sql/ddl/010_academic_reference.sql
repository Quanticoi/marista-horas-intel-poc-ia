-- Additive source staging. Reference planning is never an enrollment label.
CREATE TABLE planning.academic_source_files (
 sha256 text PRIMARY KEY CHECK (sha256 ~ '^[0-9a-f]{64}$'),
 filename text NOT NULL, byte_count bigint NOT NULL CHECK (byte_count > 0),
 source_type text NOT NULL DEFAULT 'REFERENCE_PLANNING_OR_CONTRACT',
 ingested_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE planning.academic_reference_rows (
 source_row_id uuid PRIMARY KEY,
 source_file_sha256 text NOT NULL REFERENCES planning.academic_source_files(sha256),
 source_sheet text NOT NULL, source_row_number integer NOT NULL CHECK (source_row_number > 0),
 offer_id uuid NOT NULL, status text NOT NULL CHECK (status IN ('REFERENCE_ONLY','QUARANTINED')),
 payload jsonb NOT NULL,
 UNIQUE(source_file_sha256,source_sheet,source_row_number)
);
CREATE INDEX academic_reference_offer ON planning.academic_reference_rows(offer_id);
CREATE TABLE planning.academic_data_dictionary (
 source_file_sha256 text NOT NULL REFERENCES planning.academic_source_files(sha256),
 source_row_number integer NOT NULL,
 entity_name text NOT NULL, field_name text NOT NULL, payload jsonb NOT NULL,
 PRIMARY KEY(source_file_sha256,source_row_number)
);
CREATE VIEW planning.v_academic_reference_activities AS
 SELECT source_row_id,offer_id,source_file_sha256,source_sheet,source_row_number,status,
 payload->>'course_code' AS course_code,payload->>'curriculum_code' AS curriculum_code,
 payload->>'discipline_code' AS discipline_code,payload->>'shift' AS shift,
 payload->>'activity_type' AS activity_type,payload->>'division_label' AS division_label,
 (payload->>'planned_students')::integer AS reference_planned_students,
 (payload->>'offered_seats')::integer AS reference_offered_seats,payload->'issues' AS issues
 FROM planning.academic_reference_rows;
CREATE VIEW planning.v_academic_reference_offers AS
 SELECT offer_id, payload->>'course_code' AS course_code,
 payload->>'curriculum_code' AS curriculum_code,payload->>'discipline_code' AS discipline_code,
 payload->>'shift' AS shift, count(*) AS source_activity_rows,
 bool_or(status='QUARANTINED') AS requires_review,
 jsonb_agg(jsonb_build_object('source_row_id',source_row_id,'source_row_number',source_row_number,
   'activity_type',payload->>'activity_type','division_label',payload->>'division_label',
   'reference_planned_students',payload->'planned_students','reference_offered_seats',payload->'offered_seats')
   ORDER BY source_row_number,source_row_id) AS activities
 FROM planning.academic_reference_rows
 GROUP BY offer_id,payload->>'course_code',payload->>'curriculum_code',payload->>'discipline_code',payload->>'shift';
GRANT SELECT,INSERT ON planning.academic_source_files,planning.academic_reference_rows,planning.academic_data_dictionary TO planning_app;
GRANT SELECT ON planning.academic_source_files,planning.academic_reference_rows,planning.academic_data_dictionary,
 planning.v_academic_reference_activities,planning.v_academic_reference_offers TO planning_readonly;
GRANT SELECT ON planning.v_academic_reference_activities,planning.v_academic_reference_offers TO planning_app;
