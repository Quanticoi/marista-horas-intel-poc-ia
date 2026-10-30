# Troubleshooting Compose

| Sintoma | Ação |
|---|---|
| Daemon inacessível | Abrir Docker Desktop; docker --context desktop-linux info |
| Conflito Rancher | Executar um runtime por vez; desativar integração WSL com distros Rancher |
| Unhealthy | docker compose ps -a e docker compose logs --tail 100 SERVICO |
| Senhas falham | Preservar .env correspondente aos volumes |
| MLflow vazio | Selecionar experimento; Default está vazio |
| Registry integer=VARCHAR | Rebuild com launcher psycopg2 |
| SciPy _lazywhere | Rebuild com scipy1.15.2 fixado |
| Artefatos indisponíveis | Conferir RustFS, bucket e credenciais |
| Batch pendente | Corrigir broker/worker antes de tools recover |
| Alias divergiu | tools reconcile com operador/motivo |
| Dashboard logs antigos | Histórico importado; atuais via docker compose logs |

Não usar reset/unregister/prune como reparo genérico. Warnings não significam falha
quando testes e validação retornam PASS.
