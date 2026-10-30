# Windows

Docker Desktop com engine Linux/WSL2, Docker Compose, Git e Python 3.11+ para os utilitários de validação.

Na raiz do PowerShell:

1. docker --context desktop-linux info
2. $env:DOCKER_CONTEXT = "desktop-linux"
3. Set-ExecutionPolicy -Scope Process Bypass
4. ./deployment/scripts/compose.ps1 init

Na instalação existente, a atualização C3 exige build, migrate, start e validate.
[Operação](../commands/DOCKER_COMPOSE.md) e [notebook/publicação C3](../operations/C3_TRAINING.md).
Aplicação/testes funcionais executam nos containers. Python 3.11+ local é necessário
para geradores estáticos e o verificador read-only de acessos HTTP (biblioteca padrão).
