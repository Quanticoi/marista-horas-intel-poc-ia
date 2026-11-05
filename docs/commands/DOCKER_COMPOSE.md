# Operação Docker Compose

Execute na raiz. PowerShell usa `desktop-linux` por padrão; `DOCKER_CONTEXT`
permite selecionar outro contexto. Serviços executam em containers.

| Comando `compose.ps1` | Efeito |
|---|---|
| `init` | Prepara credenciais ausentes, imagens, bancos/bucket, migrations, seed legada, serviços e testes |
| `build` | Constrói as imagens da aplicação e do Jupyter |
| `rebuild` | Build, bootstrap/migrations/seed idempotentes e healthchecks; preserva volumes; não treina |
| `start` / `stop` | Sobe com espera de saúde / para preservando dados |
| `restart -Service api` | Reinicia o serviço indicado |
| `status` / `logs -Service mlflow` | Inventário / acompanhamento de logs |
| `migrate` | Atualiza schema acadêmico e backend MLflow pelo mecanismo oficial |
| `journey` | Executa 00–06, incluindo treino; 07–10 ficam para decisão/execução explícitas |
| `test` | Suítes com serviços e evidências disponíveis; verificação de acessos |
| `validate` | Healthchecks, dependências e testes |
| `acceptance` | Testa, reinicia MLflow, testa, reconstrói e testa persistência; não reseta |
| `check` | Confere a configuração Compose |

```powershell
.\deployment\scripts\compose.ps1 start
.\deployment\scripts\compose.ps1 status
.\deployment\scripts\compose.ps1 logs -Service api
```

Os testes com modelos/resultados existentes usam evidências identificadas; um reset
invalida os IDs de ensaios anteriores. Após reset, execute a jornada V4 para produzir
novas evidências. A prova específica de preservação da origem está no ensaio isolado.

O comando legado `publish` existe para APIs dedicadas antigas. Na V4, disponibilize
versões pelo notebook 08, no serviço de inferência compartilhado. Não use `tools train`
ou `tools retrain`: o treinamento operacional foi desativado.

[Reset seletivo](../operations/RESET_POC.md) é separado de rebuild. Volumes nomeados
guardam PostgreSQL, RustFS e RabbitMQ. Workspace e relatórios ficam no projeto.
