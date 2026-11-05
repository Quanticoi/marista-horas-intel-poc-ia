# Logs e diagnóstico

Eventos estruturados de Workbench, API, worker e inferência usam IDs de correlação.
O dashboard em http://localhost:8088 lê `data/compose-logs/*.jsonl`. Logs completos:

```powershell
docker compose logs -f --tail 100 api worker inference
docker compose logs --since 10m mlflow rustfs
```

Ctrl+C encerra só o acompanhamento. Logs Docker têm rotação de três arquivos de
10 MB; auditoria de negócio permanece no PostgreSQL. Os Traces MLflow detalham
operações e duração, separados das métricas de treinamento.

`data/reference/` contém as planilhas locais; `data/compose-logs/`, eventos.
Modelos e manifests ficam no RustFS. [Repetição e Traces](EXPERIMENTS_AND_TRACING.md).
