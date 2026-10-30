# Operação Compose

Migração concluída. Não repetir export/restore/cleanup. Preserve .env e .runtime/migration.
Use Docker Desktop, Rancher fechado e DOCKER_CONTEXT=desktop-linux no Windows.

| compose.ps1 | Uso |
|---|---|
| init | Instalação nova: credenciais se ausentes, build, bancos/bucket, testes |
| build | Reconstruir duas imagens |
| migrate | Migrar schemas acadêmico e MLflow |
| publish -ModelKey CHAVE | Criar/atualizar API exclusiva do modelo aprovado |
| start | Subir/atualizar e aguardar saúde |
| stop | Parar preservando dados |
| restart -Service api | Reiniciar serviço |
| status | Inventário |
| logs -Service mlflow | Logs contínuos |
| validate | Dependências/pip check por instância e unitários/integração |
| test | Testes com serviços já prontos |
| check | Validar Compose sem daemon |

Script: deployment/scripts/compose.ps1. Na instalação migrada use start.
Atualização: build, migrate, start e validate. Não muda aprovações nem restaura bancos.
Volumes nomeados: PostgreSQL/RustFS/RabbitMQ. workspace/ é bind mount do Jupyter.
Dashboard lê logs históricos; atuais via docker compose logs. Rotação 3×10MB.
Healthchecks testam dependências reais. depends_on service_healthy ordena startup;
falhas posteriores aparecem unhealthy, sem reconciliação automática.
Não usar down -v no ambiente com dados.

CI em .github/workflows/compose.yml. E2E exige aprovação humana e é explícito.
Backups originais em .runtime/migration; scripts da migração concluída removidos.
[Validação dos acessos](../operations/ACESSOS.md): python deployment/scripts/check_access.py.

[Fluxo C3 e APIs dedicadas](../operations/C3_TRAINING.md). Após publicar modelos, o script inclui
automaticamente `.runtime/models.compose.json`; comandos Docker diretos precisam dos dois `-f`.
