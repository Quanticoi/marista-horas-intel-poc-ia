-- Read-only. No MLflow metadata tables are accessed.
SELECT filename,sha256,byte_count FROM planning.academic_source_files ORDER BY filename;
SELECT course_code,shift,count(*) AS activity_rows
FROM planning.v_academic_reference_activities GROUP BY course_code,shift ORDER BY course_code;
SELECT * FROM planning.v_academic_reference_offers
WHERE course_code='2248' AND discipline_code='P164';
SELECT * FROM planning.v_academic_reference_activities WHERE status='QUARANTINED'
ORDER BY course_code,source_row_number;
SELECT count(DISTINCT entity_name) AS entities,count(*) AS fields
FROM planning.academic_data_dictionary;
