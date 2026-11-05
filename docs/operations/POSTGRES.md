# PostgreSQL: origem, operação e proposta final

Uma instância `postgres:15.10-bookworm` hospeda os dois bancos em volume persistente.
Não há porta pública no host. Abra o console:

```powershell
docker compose exec postgres psql -U postgres -d planejamento_db
```

| Grupo | Banco/schema e tabelas |
|---|---|
| Referências | `planejamento_db.planning.academic_source_files`, `academic_reference_rows`, `academic_data_dictionary` |
| Origem sintética | `academic_simulation_snapshots`, `model_training_observations` |
| Ciência | `workbench_campaigns`, `workbench_models` |
| Operação | `operation_jobs`, `model_approval_requests`, `academic_deployments` |
| Proposição final da IA | `ai_proposals_v2`, `ai_proposal_offers_v2` |
| MLflow | `mlflow_db`, administrado exclusivamente pelo MLflow |

Consultas de conferência:

```sql
SELECT snapshot_id,cycle_code,seed,dataset_sha256 FROM planning.academic_simulation_snapshots;
SELECT campaign_id,request_key,status,run_id FROM planning.workbench_campaigns ORDER BY created_at DESC;
SELECT proposal_id,cycle_code,revision,status,payload_sha256,manifest_uri FROM planning.ai_proposals_v2 ORDER BY generated_at DESC;
SELECT proposal_id,count(*) AS ofertas FROM planning.ai_proposal_offers_v2 GROUP BY proposal_id;
```

Consultas parametrizadas: [observações V4](../../sql/queries/v4_observations.sql) e
[validação da proposta](../../sql/queries/v4_proposal_validation.sql).
Compare os IDs e contagens com a API e use o notebook 10 para verificação de hashes.
Não execute DDL/UPDATE sobre tabelas internas MLflow. Migrations acadêmicas são aditivas.
