# Jornada Planilha Turmas — Docker Compose

Esta jornada executa no Docker Compose e demonstra leitura SQL, treinamento,
registro de modelo, inferência e persistência da proposta com rastreabilidade.

## Executar

Na raiz, com Docker Desktop ativo e o `.env` existente preservado:

```powershell
.\deployment\scripts\compose.ps1 rebuild
.\deployment\scripts\compose.ps1 acceptance
```

`rebuild` constrói as duas imagens, aguarda PostgreSQL/RustFS/RabbitMQ, cria bancos
e papéis se ausentes, aplica Alembic, garante bucket e seed, sobe serviços,
verifica dependências e executa o notebook em kernel novo com testes de integração.
O MLflow executa seu próprio `mlflow db upgrade` antes de abrir a porta HTTP.
`acceptance` executa a jornada, reinicia MLflow, verifica a mesma geração, faz
rebuild e verifica novamente a mesma geração. Não remove volumes.

Instalação nova: `compose.ps1 init` gera credenciais somente quando `.env` não
existe. Nunca gere novas senhas para volumes existentes. Para uso diário:
`compose.ps1 start`, `status`, `journey`, `stop`. Não usar `down -v`.
Em Linux: `DOCKER_CONTEXT=default sh deployment/scripts/journey.sh rebuild`
com `.env` previamente configurado; `journey` e `acceptance` também disponíveis.

Abra [Jupyter](http://127.0.0.1:8888/lab/tree/notebooks/01_jornada_completa_planilha_turmas.ipynb)
e execute **Restart Kernel and Run All**. A pasta `notebooks/` no Jupyter contém a cópia editável da Jornada Completa. Cópias de trabalho
existentes não são sobrescritas durante rebuild. A execução automatizada usa
`/app/notebooks/01_jornada_completa_planilha_turmas.ipynb`, salva o notebook executado
em `artifacts/reports` e o resumo também no MLflow.

## Configuração e persistência

`compose.yaml` é a configuração central do runtime. `.env.example` lista os
segredos necessários sem valores. Endereços internos abaixo são resolvidos pelo
DNS da rede Compose; `127.0.0.1` serve somente ao navegador no host.

| Configuração / componente | Destino e responsabilidade |
|---|---|
| `SOURCE_DATABASE_URL` | PostgreSQL `postgres:5432/planejamento_db`, papel `planning_readonly`; o notebook abre a conexão SQL |
| `APPLICATION_DATABASE_URL` | Mesmo banco, papel `planning_app`; grava proposta em transação |
| `MLFLOW_TRACKING_URI` | `http://mlflow:5000`; SDK e Registry, MLflow 3.11.1 em ambos os lados |
| `MLFLOW_UI_BASE_URL` | `http://127.0.0.1:5000`, links no notebook |
| `MLFLOW_EXPERIMENT_NAME` | `planilha-turmas-proxy-v1`; diagnóstico usa experimento separado |
| `MODEL_NAME` | `planilha-turmas-demo`, versão explícita, sem promoção |
| `API_URI` / `INFERENCE_URI` | `http://api:8000` / `http://inference:8001` |
| `JOURNEY_MODE` | `DEMO`; REAL é rejeitado até existir contrato de fonte validado |
| `JOURNEY_CYCLE` / `JOURNEY_COURSE` | Default `2026-1` / todos; filtro opcional pelo UUID do curso |
| `JOURNEY_TIMEOUT` / `JOURNEY_RETRIES` | 15 segundos / 2 retries; inferência até 120 segundos |
| Metadados MLflow | `mlflow_db`, schema administrado exclusivamente pelo MLflow |
| Fonte e negócio | `planejamento_db.planning`: catálogo, histórico, snapshots, `proposal_generations`, `proposal_lines` |
| Metadados operacionais IA | `planejamento_db.planning`: tabelas existentes de execuções, deployments, jobs e auditoria |
| Artefatos | RustFS `pucpr-poc/mlflow`; SDK envia ao proxy e somente MLflow grava o modelo |
| Dados físicos | Volumes Compose `postgres`, `rustfs`, `rabbitmq`; workspace e reports em bind mounts preservados |
| Eventos | `data/compose-logs/*.jsonl`, sanitizados, consultáveis no dashboard por `correlation_id` |

Credenciais são interpoladas do
`.env` para os containers; este arquivo não é versionado. Não publique a saída de
`docker compose config` nem `docker inspect` com configurações completas.

## Dados, modelo e rastreabilidade

`src/data/synthetic.py`, seed 42 e `config/training.yaml` produzem histórico
reproduzível 2020–2025, persistido por `tools seed`. A consulta versionada
`sql/queries/journey_history.sql` recebe snapshot, ciclo e curso. Retorna UUIDs de
curso/período/disciplina, índice de semestre, semestre e total de estudantes.
Nulos, chaves duplicadas, ausência de dados e períodos inválidos bloqueiam o fluxo.

O último semestre histórico avalia o Ridge; os anteriores ajustam one-hot,
padronização e regressão. O conjunto futuro só contém chaves e período-alvo.
MAE/RMSE são calculados sobre previsões reais; os resultados DEMO não representam
qualidade institucional. O modelo completo é registrado com assinatura/exemplo,
removido da memória e recarregado pela versão explícita no notebook e no serviço
de inferência existente. A resposta distingue `loaded` de `operationally_promoted`.

Regra provisória POC: cada disciplina recebe a demanda de todo o período;
estudantes propostos = `max(0, ceil(previsão))`; turmas = `ceil(estudantes/40)`.
Esta regra não constitui decisão aprovada do MER. Previsão bruta, composição e
ajuste humano ficam separados; o estado inicial é DRAFT.

O UUID da execução é a chave idempotente. Repetir o mesmo payload retorna a mesma
geração; payload diferente com o mesmo UUID falha. Novo Run All cria UUID e versão
novos, preservando gerações anteriores. A transação grava cabeçalho, linhas e
auditoria integralmente; o fluxo não atualiza propostas nem revisões humanas.

## API e C3

Todas as rotas requerem `Authorization: Bearer <API_TOKEN>`; o notebook transmite
também `X-Correlation-ID` igual a `execution_id`.

| Request | Response |
|---|---|
| `GET /v1/proposals/{execution_id}` | Cabeçalho com ciclo, snapshot/hash, run/experimento, modelo/versão, regra, status, data e quantidade de linhas |
| `GET /v1/proposals/{execution_id}/lines?limit=100&offset=0` | Linhas do PostgreSQL com chaves acadêmicas, previsão bruta, estudantes/turmas propostos e ajuste humano |
| `GET /v1/proposals?cycle=2026-1&course_id=<uuid>&limit=100&offset=0` | Linhas e rastreabilidade filtradas por ciclo e curso opcional |

Limite 1–500, offset >= 0. Códigos: 200 sucesso, 401 sem autenticação, 404 geração
inexistente, 422 parâmetros inválidos, 503 dependência indisponível. Lista sem
resultados retorna `[]`. A consulta não executa treinamento.

| Etapas do notebook | Componente C3 demonstrado |
|---|---|
| 1–3: dependências, SQL, preparação | Jupyter + PostgreSQL + dataset/snapshot |
| 4–6: modelo, experimento, fit/avaliação | Processamento Python + MLflow Tracking |
| 7: persistência e versão | MLflow Registry + RustFS + backend PostgreSQL |
| 8: reload e HTTP | Serviço de inferência existente, versão verificável |
| 9–10: composição e transação | Regra provisória + persistência da Planilha Turmas |
| 11–12: consulta e evidências | API + dashboard HTML + correlação ponta a ponta |

Não foram fornecidos IDs oficiais das US; não se atribui cobertura funcional
inventada. Os módulos do fluxo de aprovação/publicação operacional continuam
preservados, separados da geração DRAFT desta demonstração.

## Acessos e diagnóstico

[MLflow](http://127.0.0.1:5000) · [API](http://127.0.0.1:8000/docs) ·
[Dashboard](http://127.0.0.1:8088) · [RustFS](http://127.0.0.1:9001).
Credenciais continuam no `.env`, nunca nos links.

```powershell
.\deployment\scripts\compose.ps1 status
.\deployment\scripts\compose.ps1 logs -Service mlflow
docker --context desktop-linux compose logs --tail 100 postgres rustfs api inference
```

Falhas reais e resultados de aceite são registrados em `history/state.md` e
`artifacts/reports`. Os testes simulam MLflow indisponível por uma porta fechada
dentro do container; não desligam serviços de outros projetos. Reinício/rebuild
de aceite atua somente no projeto Compose `marista`.
