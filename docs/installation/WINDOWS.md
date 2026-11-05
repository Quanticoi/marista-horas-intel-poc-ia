# Instalação no Windows

Use Docker Desktop com engine Linux/WSL2, Git e Python 3.11/3.12 para scripts
administrativos. Reserve inicialmente 8 GiB para Docker. Não instale os serviços
Python/MLflow diretamente no Windows.

Clone o repositório, entre na raiz e coloque as três planilhas em `data/reference/`.
Em PowerShell:

```powershell
docker --context desktop-linux info
$env:DOCKER_CONTEXT = 'desktop-linux'
.\deployment\scripts\compose.ps1 init
```

Se a política local bloquear scripts, habilite a execução conforme a política da
máquina. `init` prepara o `.env` se ausente; não troque credenciais de volumes existentes.
Atualizações usam `compose.ps1 rebuild`; uso diário, `compose.ps1 start`.

Abra [Jupyter](http://localhost:8888/lab/tree/notebooks/00_ambiente.ipynb).
[Acessos](../operations/ACESSOS.md) · [Runbook V4](../operations/POC_V4_MANUAL_RUNBOOK.md).
