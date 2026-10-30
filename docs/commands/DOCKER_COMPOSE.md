# Operação Compose

Execute na raiz do projeto. No Windows, os scripts usam Docker Desktop e o contexto desktop-linux por padrão; DOCKER_CONTEXT permite selecionar outro contexto.

| compose.ps1 | Uso |
|---|---|
| init | Instalação nova: credenciais se ausentes, build, bancos/bucket, testes |
| build | Reconstruir duas imagens |
| rebuild | Construir, migrar, subir e executar jornada/testes preservando volumes |
| journey | Executar notebook em kernel novo e testes da jornada |
| acceptance | Verificar a mesma geração após reinício MLflow e rebuild |
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

Script: deployment/scripts/compose.ps1. Para uso diário, start. Antes do primeiro test/validate, execute init, rebuild ou journey para gerar o relatório utilizado nos testes.
Atualização: build, migrate, start e validate. Não muda aprovações nem restaura bancos.
Volumes nomeados: PostgreSQL/RustFS/RabbitMQ. workspace/ é bind mount do Jupyter.
Dashboard lê eventos atuais da jornada, API e inferência por correlation_id; logs completos via docker compose logs. Rotação 3×10MB.
Healthchecks testam dependências reais. depends_on service_healthy ordena startup;
falhas posteriores aparecem unhealthy, sem reconciliação automática.
Não usar down -v no ambiente com dados.

CI em .github/workflows/compose.yml. E2E exige aprovação humana e é explícito.
Backups originais em .runtime/migration; scripts da migração concluída removidos.
[Validação dos acessos](../operations/ACESSOS.md): python deployment/scripts/check_access.py.

[Fluxo C3 e APIs dedicadas](../operations/C3_TRAINING.md). Após publicar modelos, o script inclui
automaticamente `.runtime/models.compose.json`; comandos Docker diretos precisam dos dois `-f`.
