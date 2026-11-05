# Acessos locais

Os valores reais estão no `.env` da raiz. `.env.example` documenta os nomes.
As portas são publicadas em loopback; dentro dos containers, use DNS Compose.

| Serviço | Navegador / host | Autenticação |
|---|---|---|
| Jupyter | http://localhost:8888/lab/tree/notebooks/00_ambiente.ipynb | `JUPYTER_TOKEN` |
| MLflow | http://localhost:5000 | Sem login HTTP na POC local |
| RustFS console | http://localhost:9001 | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` |
| RustFS S3 | http://localhost:9000 | Cliente S3 com assinatura; não é a console |
| API OpenAPI | http://localhost:8000/docs | Bearer `API_TOKEN`; revisão/deploy usam `OPERATOR_TOKEN` |
| Inferência | http://localhost:8001/ready | Readiness público; `/internal/academic/predict` exige `INFERENCE_TOKEN` |
| Dashboard | http://localhost:8088 | `DASHBOARD_TOKEN` |
| RabbitMQ | http://localhost:15672 | Usuário `poc`; `RABBITMQ_PASSWORD` |
| Monitoramento | http://localhost:8010/v1/status | Bearer `MONITOR_TOKEN` |
| Ingestion legado | http://localhost:8020/docs | Bearer `INGESTION_TOKEN` |
| PostgreSQL | Apenas rede interna | Console via `docker compose exec postgres psql -U postgres -d planejamento_db` |

Uma página `/docs` acessível não torna as rotas de negócio públicas. No Swagger,
informe o header Authorization conforme o parâmetro da rota. Não exponha credenciais
em links, células, screenshots ou relatórios. O worker não tem interface web.

Verificação autenticada e negativa sem imprimir credenciais:

```powershell
python deployment/scripts/check_access.py
```

O script grava apenas status em `artifacts/reports/access-check.json`. A consulta
de inferência usa payload inválido para conferir autenticação sem criar previsão.
[RustFS](RUSTFS.md) · [MLflow](MLFLOW.md).
