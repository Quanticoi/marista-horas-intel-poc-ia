# Comandos frequentes V4

Na raiz do repositório:

| Objetivo | Comando |
|---|---|
| Subir | `.\deployment\scripts\compose.ps1 start` |
| Atualizar preservando dados | `.\deployment\scripts\compose.ps1 rebuild` |
| Ver serviços | `docker compose ps` |
| Diagnosticar | `docker compose logs --tail 100 api worker inference mlflow` |
| Conferir acessos | `python deployment/scripts/check_access.py` |
| Conferir fontes/configuração | `python deployment/scripts/validate_static.py` |
| Treinar | Notebook 04 ou 05, modo NEW ou RESUME explícito |
| Aprovar / disponibilizar | Notebooks 07 / 08 |
| Consumir / auditar | Notebooks 09 / 10 |
| Planejar limpeza dos ensaios | `python deployment/scripts/reset_poc.py preview --environment poc --project marista --mode reset-experiments` |
| Testar limpeza isolada | `python tests/acceptance/v4_adjustments.py --reset-isolated` |

O preview não apaga; siga [o procedimento de execução](../operations/RESET_POC.md).
[Todos os comandos Compose](DOCKER_COMPOSE.md) · [Testes de jornada](../operations/POC_V4_MANUAL_RUNBOOK.md).
