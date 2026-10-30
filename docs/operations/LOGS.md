> Jornada atual (30/10/2026): veja [JOURNEY.md](JOURNEY.md). Notebook principal 01_jornada_completa_planilha_turmas; Docker Compose; eventos atuais no dashboard. Resultados reais e pendencias em history/state.md; validacoes historicas abaixo nao substituem o aceite atual.

# Logs

```powershell
docker compose logs -f --tail 100 api worker inference
docker compose logs --since 10m mlflow rustfs
```

Ctrl+C termina somente acompanhamento. Rotação: três arquivos de 10MB por container.
Auditoria de negócio fica no PostgreSQL. Dashboard lê JSONL históricos em
data/compose-logs; não coleta logs atuais nem monta socket Docker.
Collector Python permanece para referência Kubernetes futura.
