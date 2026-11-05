-- Canonical read models over immutable, versioned source rows. Do not duplicate source facts.
CREATE VIEW planning.academic_course_identity AS
 SELECT DISTINCT source_file_sha256,
 md5(jsonb_build_array(source_file_sha256,payload->>'establishment',payload->>'school',payload->>'course_code',payload->>'shift')::text)::uuid AS course_id,
 payload->>'establishment' AS establishment,payload->>'school' AS school,
 payload->>'course_code' AS course_code,payload->>'course_name' AS course_name,
 payload->>'shift' AS shift,NULL::text AS prime_id,'UNMAPPED'::text AS mapping_status
 FROM planning.academic_reference_rows;
CREATE VIEW planning.curriculum_identity AS
 SELECT DISTINCT r.source_file_sha256,c.course_id,
 md5(jsonb_build_array(c.course_id,r.payload->>'curriculum_code',r.payload->>'curriculum_version')::text)::uuid AS curriculum_id,
 r.payload->>'curriculum_code' AS curriculum_code,r.payload->>'curriculum_version' AS curriculum_version,
 NULL::date AS official_valid_from,NULL::date AS official_valid_until
 FROM planning.academic_reference_rows r JOIN planning.academic_course_identity c
 ON c.source_file_sha256=r.source_file_sha256 AND c.establishment=r.payload->>'establishment'
 AND c.school=r.payload->>'school' AND c.course_code=r.payload->>'course_code' AND c.shift=r.payload->>'shift';
CREATE VIEW planning.discipline_identity AS
 SELECT DISTINCT source_file_sha256,
 md5(jsonb_build_array(source_file_sha256,payload->>'discipline_code',payload->>'discipline_name')::text)::uuid AS discipline_id,
 payload->>'discipline_code' AS discipline_code,payload->>'discipline_name' AS discipline_name,
 NULL::text AS prime_id,'UNMAPPED'::text AS mapping_status FROM planning.academic_reference_rows;
CREATE VIEW planning.academic_offer AS
 SELECT r.source_file_sha256,r.offer_id,c.course_id,cu.curriculum_id,d.discipline_id,
 r.payload->>'cycle_code' AS cycle_code,r.payload->>'class_label' AS class_label,
 (r.payload->>'period')::integer AS period,r.payload->>'offer_type' AS offer_type,
 bool_or(r.status='QUARANTINED') AS requires_review,
 array_agg(r.source_row_id ORDER BY r.source_row_number) AS source_rows
 FROM planning.academic_reference_rows r JOIN planning.academic_course_identity c
 ON c.source_file_sha256=r.source_file_sha256 AND c.establishment=r.payload->>'establishment'
 AND c.school=r.payload->>'school' AND c.course_code=r.payload->>'course_code' AND c.shift=r.payload->>'shift'
 JOIN planning.curriculum_identity cu ON cu.course_id=c.course_id AND cu.curriculum_code=r.payload->>'curriculum_code'
 AND cu.curriculum_version IS NOT DISTINCT FROM r.payload->>'curriculum_version'
 JOIN planning.discipline_identity d ON d.source_file_sha256=r.source_file_sha256 AND d.discipline_code=r.payload->>'discipline_code'
 AND d.discipline_name=r.payload->>'discipline_name'
 GROUP BY r.source_file_sha256,r.offer_id,c.course_id,cu.curriculum_id,d.discipline_id,
 r.payload->>'cycle_code',r.payload->>'class_label',r.payload->>'period',r.payload->>'offer_type';
CREATE VIEW planning.offer_activity AS SELECT * FROM planning.v_academic_reference_activities;
CREATE VIEW planning.academic_cohort AS
 SELECT DISTINCT snapshot_id,cohort_id,payload->>'course_code' AS course_code,
 payload->>'curriculum_code' AS curriculum_code,payload->>'cohort_ingress' AS cohort_ingress,
 payload->>'shift' AS shift,'SYNTHETIC_ONLY'::text AS mapping_status,
 'SYNTHETIC_ROLLING_COHORT'::text AS source FROM planning.model_training_observations;
CREATE VIEW planning.offer_unification_candidate AS
 SELECT source_row_id,offer_id,source_file_sha256,payload->>'unification_suggestion' AS suggestion,
 payload->>'coordination_validation' AS reference_coordination_text,
 'CANDIDATE_PENDING_DATA'::text AS status,false AS applied,true AS requires_gqa
 FROM planning.academic_reference_rows
 WHERE payload->>'unification_suggestion' IS NOT NULL
 AND lower(trim(payload->>'unification_suggestion')) NOT IN ('não','nao','-','');
CREATE VIEW planning.academic_mapping AS
 SELECT source_row_id,source_file_sha256,payload->>'course_code' AS excel_course_code,
 payload->>'curriculum_code' AS excel_curriculum_code,payload->>'discipline_code' AS excel_discipline_code,
 NULL::text AS prime_course_id,NULL::text AS prime_discipline_id,'UNMAPPED'::text AS status
 FROM planning.academic_reference_rows;
GRANT SELECT ON planning.academic_course_identity,planning.curriculum_identity,planning.discipline_identity,
 planning.academic_offer,planning.offer_activity,planning.academic_cohort,
 planning.offer_unification_candidate,planning.academic_mapping TO planning_app,planning_readonly;
