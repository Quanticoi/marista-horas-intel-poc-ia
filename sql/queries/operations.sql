-- Sugestões com proveniência
SELECT c.cycle_code, mc.model_key, md.registered_version,
       ds.snapshot_key, p.forecast_students, os.estimated_total,
       os.status, p.predicted_at
FROM planning.offer_suggestions os
JOIN planning.predictions p ON p.id=os.prediction_id
JOIN planning.academic_cycles c ON c.id=os.cycle_id
JOIN planning.model_catalog mc ON mc.id=p.model_id
JOIN planning.model_deployments md ON md.id=p.deployment_id
JOIN planning.dataset_snapshots ds ON ds.id=p.snapshot_id
ORDER BY p.predicted_at DESC LIMIT 100;

-- Jobs e pendências
SELECT status, count(*) AS jobs, max(requested_at) AS ultimo
FROM planning.prediction_jobs GROUP BY status ORDER BY status;

-- 30 modelos previstos
SELECT count(*) AS modelos, count(*) FILTER (WHERE active) AS ativos
FROM planning.model_catalog;
