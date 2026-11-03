# Logs

Notebook, API e inferência gravam eventos JSONL em `data/compose-logs`, com
sanitização de credenciais e `correlation_id` comum à execução. O dashboard
consulta esses arquivos para exibir as etapas e resultados da jornada.

```powershell
docker compose logs -f --tail 100 api worker inference
docker compose logs --since 10m mlflow rustfs
```

Ctrl+C encerra apenas o acompanhamento. Logs completos dos containers têm rotação
de três arquivos de 10 MB. A auditoria de negócio permanece no PostgreSQL.
`data/compose-logs` é a única pasta de dados locais utilizada pelo Compose;
datasets e modelos ficam no PostgreSQL e no RustFS.
