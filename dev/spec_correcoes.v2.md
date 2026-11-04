# SPEC — Correções V2 da POC IA | Horas Inteligentes

**Arquivo:** `spec_correcoes.v2.md`  
**Versão:** 2.0  
**Data:** 04/11/2026  
**Destino:** Codex — `Quanticoi/marista-horas-intel-poc-ia`, branch `development`  
**Natureza:** especificação executável de correção, implementação, testes e aceite  
**Objetivo:** validar a arquitetura C2/C3 de IA proposta para o Grupo Marista/PUCPR, com o Jupyter como bancada central do cientista e evidências auditáveis de ponta a ponta.

> **MANDATO:** esta V2 complementa e corrige a `dev/spec-correcoes.md` V1.1. Não recrie o projeto nem considere a simples existência de notebook, endpoint, tag ou teste como funcionalidade concluída. Inspecione primeiro o código da `development` e implemente as jornadas operacionais que faltam. Preserve dados, modelos, histórico, volumes, `.env`, backups e notebooks pessoais. Toda operação destrutiva exige autorização humana separada. **Não execute nenhum reset da POC principal durante esta tarefa.** Não promover automaticamente modelos nem inventar regras de negócio ausentes. Não abrir mão de testes reais para declarar `PASS`.

## 0. Referências, precedência e fotografia do estado atual

### 0.1 Fontes

1. Repositório `https://github.com/Quanticoi/marista-horas-intel-poc-ia` na branch `development`. Ler `README.md`, `compose.yaml`, `dev/generate_compose.py`, `dev/spec-correcoes.md`, `notebooks/*`, `src/*`, `sql/*`, `tests/*`, `docs/*`, `artifacts/reports/correcoes-v1.1-acceptance.md` e JSON de aceite.
2. Arquitetura de Componentes V3, Arquitetura de Containers V3 e Diagrama de Sequência V3 fornecidos pelo projeto.
3. `REQ_InteligenciaeOtimizacaodeHorariosAcademicos_V4.4`, de 25/09/2026.
4. ADRs e contratos versionados do repositório, em especial `docs/adr/009-lineage-contract.md`, `docs/architecture/LINEAGE.md`, `docs/architecture/FUNCTIONAL_COVERAGE.md`, `docs/contracts/`.

**Precedência:** V4.4 governa critérios funcionais; V3 define responsabilidades arquiteturais-alvo; decisões vigentes do repositório definem runtime atual (Docker Compose). A V2 exige corrigir implementações incompletas mantendo compatibilidade. Toda divergência nova deve ser registrada em ADR/relatório, não resolvida silenciosamente.

### 0.2 Diagnóstico comprovado em 04/11/2026

| Área | Implementação encontrada | Lacuna que a V2 deve fechar |
|---|---|---|
| Jornada 01 | SQL → Ridge → MLflow → RustFS → inferência → PostgreSQL → API, com evidências | Preservar e tornar reutilizável sem depender de células para casos de uso |
| Notebook 02 | GET `application-view`, paginação, checks HTTP/SQL/S3; POST opt-in de predição isolada | **Não inicia nova geração/persistência de proposta via API** |
| Notebook 05 | Consulta `/v1/models` e exibe `campaign_scheduler=NOT_IMPLEMENTED` | **Não executa campanhas com estado, fila, retries e checkpoint** |
| Notebook 04 | Treinamento individual opt-in simples | Falta seleção explorável, parâmetros, relatório e comparação de treinamento |
| Notebook 07 | Consulta Registry; promoção pelo CLI externo | Falta jornada de revisão e solicitação de promoção auditável no notebook |
| Notebook 09 | Exibe plano de reset gerado no host | Falta UX para inventário, acompanhamento e verificação; execução deve continuar externa ao kernel |
| HI-LINEAGE/1.0 | IDs, grafo, `proposal_model_usage`, manifestos, lookup autenticado | Falta exploração intuitiva bidirecional e verificação de completude |
| API Planilha Turmas | Contrato provisório Pydantic/JSON Schema e GET de proposta | Falta geração via endpoint de negócio e fechamento de ciclo POST → persistência → GET |
| Escala | 30 treinamentos reais; 500 **identidades** em inventário | Não há 500 treinamentos reais, concorrência sustentada, checkpoint ou benchmark de serving |
| CI | Workflow GitHub Actions recente com sucesso | Não confundir CI verde com aceite dos requisitos funcionais ou de carga |

**Estado de referência do GitHub no momento da revisão:** commit `9306f1423a32...` na `development`; workflow `41859110682` concluído com sucesso. Confirmar HEAD antes de iniciar e registrar o SHA efetivamente alterado/testado; não presumir que esse estado continua igual.

## 1. Resultado obrigatório: três jornadas demonstráveis

**Jornada A — Cientista/treinamento:** Jupyter → consulta SQL/snapshot → preparação → treino real → métricas e parâmetros no MLflow → registro de versão → binário versionado no RustFS → prova de download/hash. Deve funcionar com um modelo individual e uma campanha.

**Jornada B — Serviço de IA/Planilha Turmas:** Jupyter **como cliente de teste**, não como executor de persistência → `POST` autenticado na **API Serviços Inteligentes** para gerar uma proposta DEMO → API/worker resolve snapshot e versão(s) permitida(s) → serviço de inferência carrega binário persistido → previsão → composição conforme regras DEMO explicitadas → persistência atômica em PostgreSQL → `GET application-view` retorna representação exatamente consumível pela aplicação → notebook reconcilia HTTP/SQL/MLflow/RustFS.

**Jornada C — Operação e governança:** catálogo/experimentos → modelos candidatos e versões → aprovação humana explicitamente autenticada e auditada → inferência da versão aprovada → tracing/lineage reverso → reset seguro em ambiente *descartável* → rebootstrap → nova jornada A e B. Não misturar a promoção com simples registro de modelo.

### 1.1 Critérios de conclusão globais

- Cada jornada deve ser executável por pessoa nova a partir do README, sem editar código-fonte de produção nem executar SQL manual para “completar” a jornada.
- Nunca declarar `PASS` para recurso com `NOT_IMPLEMENTED`, `NOT_EXECUTED`, mock ou somente endpoint de leitura. Usar estados `PASS`, `FAIL`, `PARTIAL`, `NOT_IMPLEMENTED`, `NOT_EXECUTED`, `NOT_EVALUATED` com evidência e limitação.
- Preservar a jornada 01 existente e seus resultados; acréscimos não podem apagar histórico ou alterar retroativamente proposta original.
- A arquitetura-alvo V3 mantém API/worker responsável pela orquestração do ciclo operacional. O notebook 01 pode conservar escrita DEMO legada por compatibilidade, mas **o caminho de aceite novo da Jornada B não pode escrever diretamente no Postgres a partir do Jupyter**.
- Não declarar conformidade integral à V4.4 sem dados/contratos suficientes; demonstrar subconjunto formal, identificar não avaliados.

## 2. Fronteiras de responsabilidade e desenho de execução

| Componente | Executa | Armazena / publica |
|---|---|---|
| JupyterLab (futuro Workbench) | Exploração, experimentação, submissão de jobs, comparação, teste API, auditoria | Notebooks e relatórios; não assume escrita operacional do worker |
| Treinador/job | Recebe modelo-chave, snapshot, configuração, treina e avalia; pode ser assíncrono | MLflow Tracking/Registry, evidências e estado da campanha |
| MLflow | Experimentos, runs, parâmetros, métricas, Registry, aliases | `mlflow_db` para metadados; RustFS para artefatos por proxy |
| RustFS (futuro Object Storage) | Armazena binários, snapshots, manifestos | Prefixos imutáveis e hash verificável; não é banco de aprovação |
| API Serviços Inteligentes | Recebe solicitação de inferência/geração, retorna protocolo/status/JSON; autoriza | Resultado via adaptador de persistência/worker |
| Serviço de inferência | Resolve modelo e versão, valida fonte/assinatura, carrega e prediz | Eventos, métricas, `inference_id`; não treina |
| Worker/compositor | Orquestra geração de proposta, regras demonstradas e idempotência | `planning.proposal_generations`, `proposal_lines`, lineage e auditoria |
| PostgreSQL de negócio | Transação, identidades, estado, referências, propostas e auditoria | `planejamento_db.planning` |
| Dashboard | Saúde, progresso, rastreabilidade e links | Consome APIs, logs e evidências; não edita resultados |

**Importante:** não criar 500 Jupyters nem 500 servidores HTTP por padrão. **Modelo registrado ≠ run de treino ≠ treinamento simultâneo ≠ API publicada.** A estratégia de inferência dedicada versus pool compartilhado é uma decisão de capacidade a ser medida, e não hipótese a impor silenciosamente ao C3.

## 3. Notebook catalogado: implementação real, não arquivos de fachada

Preservar nomes versionados abaixo e distribuição para `/workspace/notebooks` **sem sobrescrever edições do usuário**. Cópias conflitantes `.update-<hash>` exigem sinalização visível com instruções de merge para evitar que o cientista abra notebook desatualizado sem perceber.

| Notebook | Implementação mínima obrigatória | Escrita padrão |
|---|---|---|
| `00_validacao_ambiente.ipynb` | Tabela de saúde SQL, MLflow/Registry, RustFS, API, inferência, RabbitMQ, dashboard e versões; erros acionáveis | Diagnóstico controlado |
| `01_jornada_completa_planilha_turmas.ipynb` | A jornada técnica existente, com provas de persistência | Treino/proposta DEMO existente |
| `02_teste_inferencia_planilha_turmas.ipynb` | **Dois modos:** gerar proposta nova via API e consultar/validar uma existente; mostrar payload integral da aplicação | Leitura padrão; POST opt-in |
| `03_exploracao_preparacao_dados.ipynb` | SQL parametrizado, snapshot, esquema, qualidade, ausências, treino/teste temporal, gráficos/tabelas e hashes | Leitura |
| `04_treinamento_individual.ipynb` | Seleção explícita de modelo/snapshot/algoritmo/hiperparâmetros; execução real e comparação de métricas; registro e download | Treino somente opt-in |
| `05_treinamento_campanha.ipynb` | Criação, submissão, consulta, pause/resume/cancel e reprocessamento de campanha; dashboards de progresso; evidência de N treinamentos | Opt-in e persistência de estado |
| `06_avaliacao_comparativa.ipynb` | Buscar runs por filtros, comparar métricas/tempo/snapshot, qualidade temporal e eleger candidato sem promover | Leitura |
| `07_registry_governanca.ipynb` | Modelos, versões, proveniência, artefatos, status; solicitação/revisão/aprovação auditada por operador autorizado, e rollback controlado | Leitura padrão; aprovação opt-in |
| `08_auditoria_lineage.ipynb` | Buscar por proposta, run, modelo, versão, snapshot ou campanha e exibir grafo/links/checks de integridade | Leitura |
| `09_reset_total_ambiente_poc.ipynb` | Selecionar `preview`, `reset-data`, `factory-reset`, `empty`, `demo-ready`; inventário, riscos, estado/resultados e pós-verificação | `Run All` jamais apaga |

### 3.1 Requisitos de UX para todos os notebooks

- Capa com **objetivo, pré-requisitos, entradas, saídas, efeitos colaterais, risco de escrita, passo a passo e links**. Mostrar estado `READY/NOT_READY`.
- Bloco único de configuração tipada e valores de exemplo; credenciais apenas de env/secret; nunca imprimir tokens.
- Cada célula apresenta propósito e evidência esperada; funções reutilizáveis vivem em `src/`, não apenas no notebook.
- Em operações de escrita: simulação/preflight, confirmação explícita, resultado com identificadores, links e logs.
- Relatório final JSON/Markdown com UTC, commit/hash do código, IDs, status por etapa e evidência verificável.
- Executar todos os notebooks em kernel novo. Para aqueles cujo fluxo de escrita é opt-in, testar também **o modo real de escrita em ambiente descartável**, não só o modo desativado.

## 4. Correção P0 — Notebook 02: inferência completa e proposta via API

### 4.1 Modos separados

**Modo A — `READ_EXISTING` (padrão):** escolher `proposal_id`/ciclo explicitamente, GET autenticado e paginado, validar schema, dados, regras disponíveis, SQL, Registry, RustFS e lineage; não altera modelo/proposta.

**Modo B — `GENERATE_AND_VALIDATE` (opt-in):** configurar `cycle_code`, `snapshot_id`, `model_selector` (modelo e versão explicitamente liberados na DEMO ou alias aprovado), `ruleset_version`, parâmetros de capacidade DEMO, `idempotency_key`, `correlation_id` e `requester`. O notebook **faz POST em endpoint de geração**, aguarda protocolo/status ou consulta o job até conclusão, recebe `proposal_id`, executa GET application-view e valida. Não invocar diretamente `src.persistence.journey.persist()` nem montar a resposta em uma função de notebook substituindo o caminho HTTP.

**Não confundir** o `POST /internal/draft/predict` atual (retorna previsões, sem proposta persistida) com a jornada requisitada. Preservá-lo para compatibilidade. O novo caminho deve criar um objeto de proposta no banco e comprovar sua identidade em GET subsequente.

### 4.2 Contrato HTTP aditivo (sugerido; validar rotas atuais antes de implementar)

- `POST /v1/proposals/generations` — iniciar geração DEMO; request contém `schema_version`, `cycle_code`, `snapshot_id`, seletor de modelo(s), `ruleset_version`, `requested_by`; header `Idempotency-Key`. Responder `202` com `generation_job_id`, `correlation_id`, `status`, `status_url` e eventual `proposal_url` (ou `201` se síncrono justificado e documentado).
- `GET /v1/proposals/generations/{job_id}` — status `PENDING/RUNNING/COMPLETED/FAILED/CANCELLED`, etapas, tempos, mensagem sanitizada, `proposal_id` quando concluído.
- `GET /v1/proposals/{proposal_id}/application-view` — formato JSON versionado existente, com paginação estável ou envelope de exportação completa; não mudar endpoints legados.
- `GET /v1/proposals/{proposal_id}/lineage` — cadeia e integridade da proposta; paginação quando volumoso.

Preferir **API → Worker → Inferência → Compositor/Persistência**, com fila durável RabbitMQ/Celery e estado confiável no Postgres. Se uma versão mínima síncrona for necessária para fechar a POC, registrar ADR, implementar o fluxo HTTP real e manter a interface apta à execução assíncrona; **não declarar a orquestração final concluída enquanto faltarem job/status/retry**.

### 4.3 Invariantes e falhas negativas

- Reexecução com mesmo `Idempotency-Key` + payload retorna o mesmo job/proposta; chave reutilizada com payload diferente deve responder `409`.
- Persistência de cabeçalho, linhas, atribuições de modelos e auditoria em transação; falha no meio faz rollback.
- Falha após commit da proposta e antes de manifest RustFS deve permitir reparo idempotente, sem criar nova proposta.
- Modelo sem aprovação no fluxo operacional deve falhar fechado; versão explícita só em modo DEMO com autorização adequada, sem marcar como aprovada.
- Resposta de API deve ter `schema_version`, `proposal_id`, `status`, `snapshot_id`, origem dos modelos por linha, hash e regras `PASS/FAIL/NOT_EVALUATED`.
- Testar 401/403, 404, 409, 422, MLflow indisponível, artefato ausente, checksum divergente, SQL indisponível, timeout e retry.

### 4.4 Funcional V4.4 — escopo demonstrado

Validar especificamente **RGN001, RGN002, RGN003, RGN023; RF008–010, RF020–025, RF040–047, RF117–125, RF155–159, RF195–199, RF204–206; US016/017/022/026–030/033–034** conforme dados disponíveis.

- Na etapa inicial, proposta da matriz **sem docente, horário ou sala**. Não declarar modulação institucional concluída sem matriz e unificação aplicáveis.
- Distinguir alunos regulares, dependência e eletivas e suas origens somente quando fornecidos; valores faltantes como `null`/`NOT_EVALUATED`, jamais zero arbitrário.
- O `capacity=40` atual é **regra DEMO parametrizada**, não regra real da universidade.
- RGN023 exige etapas sequenciais e gate humano; na POC marcar claramente estágio inicial e não pular autorização.
- Não alterar PRIME, não matricular alunos, não efetivar publicação acadêmica.
- O contrato `poc-planilha-turmas-v1` permanece **PROVISÓRIO / PENDENTE DE HOMOLOGAÇÃO** até aprovação formal IA × Aplicação; manter schema e OpenAPI sincronizados.

## 5. Correção P0 — Notebook 05: campanhas reais e mais de 500 modelos

### 5.1 Modelo de execução

Implementar um **orquestrador mínimo persistente** de treinamento, desacoplado do kernel Jupyter. O Jupyter cria e controla campanhas; workers/job runners executam treinamento sob limite de concorrência. Usar o PostgreSQL para estados e checkpoints; RabbitMQ/Celery como transporte, nunca como único armazenamento de estado. Reutilizar SDK/treino MLflow existente.

### 5.2 Modelo relacional e API sugeridos

Reaproveitar tabelas antes de criar novas; se necessário, migration aditiva `006_training_campaigns` ou próximo número livre, com:

- `training_campaigns`: `campaign_id`, ambiente, domínio, snapshot, config hash, código, solicitante, created/started/ended UTC, status, requested_count, succeeded_count, failed_count, cancelled_count, concurrency_limit, retry_policy, correlation_id`;
- `training_campaign_items`: `campaign_id`, `model_key`, tentativa, status, `mlflow_run_id`, `registered_model_name`, `model_version`, erro sanitizado, heartbeat, tempo, identificador de job e constraints de unicidade/idempotência;
- eventos append-only de transições e checkpoints.

API `POST /v1/training/campaigns`, `GET /v1/training/campaigns/{id}`, `/items` paginado, `POST /{id}/pause`, `/resume`, `/cancel`, `/retry-failed`; documentar permissões, idempotência e limite de carga.

### 5.3 Regras operacionais obrigatórias

- Configuração `model_keys`, `snapshot_id`, algoritmos/parâmetros e `max_parallel_jobs`, com prévia de CPU/RAM e limite de concorrência conservador.
- Cada modelo treinado gera run real no MLflow, métricas, modelo registrado/versão, artefato no RustFS e lineage para campanha/snapshot; sem promoção automática.
- Estados observáveis: `CREATED`, `RUNNING`, `PAUSING`, `PAUSED`, `CANCELLING`, `CANCELLED`, `PARTIAL`, `COMPLETED`, `FAILED`; transições consistentes.
- Retomada após reinício de worker, duplicidade de entrega, timeout, falha MLflow/RustFS/SQL, retries limitados com backoff, dead-letter/sinalização, cancelamento cooperativo e deduplicação.
- `max_parallel_jobs` não é quantidade de Jupyters. Um mesmo MLflow recebe runs de muitos modelos; modelo-chave é estável e versão sempre explícita.
- Evitar 500 objetos pesados em memória no mesmo processo ou 500 serviços de inferência por padrão.

### 5.4 Aceite de escala em níveis

| Ensaio | Exigência | Declaração permitida |
|---|---|---|
| T1 | 1 modelo real: treino→Registry→RustFS→inferência | Jornada individual validada |
| T2 | 30 modelos reais: campanha, runs, artefatos, estados, retries | Campanha funcional |
| T3 | 500 **identidades** no catálogo | Apenas organização/indexação, **não escala de treino** |
| T4 | **500 treinamentos reais**, em stack descartável e orçamento de recursos controlado; registrar tempo, CPU/RAM, falhas e capacidade | Escala 500 validada **somente se T4 for realmente executado** |
| T5 | Inferência de amostra representativa das versões após restart, com carga/latência/cache; método, tamanho amostral, p95 e p99 | Evidência de serving; não equivale a 500 modelos simultâneos |

Se T4 não puder ser executado por recursos, registrar `NOT_EXECUTED` e o limite; jamais substituir 500 treinos por 500 identidades. Não executar testes de carga indiscriminadamente na POC principal.

## 6. Correção P1 — Lineage intuitivo e taxonomia cross-system

Manter `HI-LINEAGE/1.0` e migration 005 existentes. **Não inventar novos identificadores equivalentes** nem reescrever metadados históricos.

### 6.1 Dicionário canônico obrigatório

`solution_id`, `environment`, `domain`, `academic_cycle_id`, `cycle_code`, `snapshot_id`, `snapshot_sha256`, `dataset_sha256`, `training_campaign_id`, `model_key`, `experiment_id`, `run_id`, `registered_model_name`, `model_version`, `artifact_uri`, `artifact_sha256`, `code_version`, `config_hash`, `ruleset_version`, `ruleset_hash`, `inference_id`, `proposal_id`, `proposal_revision`, `correlation_id`, `trace_id`, `schema_version`.

Separar **identidade** (ID estável), **tag/label** (índice de busca), **estado** (fonte de verdade transacional) e **versão** (imutabilidade). Padronizar `snake_case`, UTC e SHA-256. Nunca guardar token, SQL confidencial ou PII em tags, object keys ou traces.

### 6.2 Onde os campos aparecem

| Sistema | Campos mínimos pesquisáveis | Navegação |
|---|---|---|
| Jupyter | `campaign_id`, `execution_id`, `proposal_id`, `model_key`, `run_id` | Links diretos e relatórios |
| MLflow run/Registry | solução/ambiente/domínio, ciclo, snapshot, campanha, modelo, código/config, versão e hashes | Run → Registry → evidência |
| RustFS | prefixos `mlflow/`, `snapshots/`, `lineage/poc/planilha-turmas/...`; manifests versionados | Chave exata, versão do objeto, SHA |
| PostgreSQL | entidades/arestas, N:N proposta↔modelo, inferência por linha, revisions, auditoria | Views/SQL + API lookup |
| API | Headers `X-Correlation-ID`, payload com IDs/versões/hashes e status | Proposta → lineage reverso |
| Logs/dashboard | correlation + job + campaign + inference + proposal IDs; status | Filtros e hiperlinks |

### 6.3 Experiência exigida no Notebook 08 / dashboard

Buscar **qualquer** `proposal_id`, `run_id`, `model_key`+versão, `snapshot_id` ou `campaign_id`, mostrar grafo `snapshot → treinamento/run → modelo registrado → inferência → proposta/linhas → contrato API`, com links clicáveis para MLflow, objeto RustFS e endpoint API. Mostrar `VERIFIED`, `LEGACY_PARTIAL`, `MISSING`, `MISMATCH` por elo, com motivo e evidência real. Suportar filtros/paginação de 500 modelos; reconciliar em ambos os sentidos, inclusive múltiplos modelos por proposta. Testar corrupção controlada de hash/mapping **somente em stack descartável**.

## 7. Correção P1 — Notebook 09 e mecanismo de reset

**Política:** o notebook é a interface de preparação e auditoria do reset; o controlador externo (`deployment/scripts/reset_poc.py`, `.ps1`, `.sh`) permanece responsável pela remoção, pois factory-reset pode terminar o kernel. Não habilitar exclusão automática por `Run All` nem criar endpoint HTTP genérico destrutivo.

### 7.1 Modos suportados

- `preview`: inventariar **sem exclusão**. Listar tabelas/contagens de `planejamento_db` e `mlflow_db`, runs, modelos, versões, traces, snapshots, objetos/versões RustFS, filas/volumes, escopo Docker, arquivos preservados e impactos.
- `reset-data` + `empty`: remover dados exclusivos da POC, inclusive runs/Registry/binários/snapshots/filas, recriar schema/serviços vazios; não deixar bancos removidos sem reconstrução.
- `reset-data` + `demo-ready`: acima, mais seed DEMO, sem treinos/modelos/propostas antigas.
- `factory-reset` + `empty`/`demo-ready`: remover **somente volumes e containers próprios validados**, reprovisionar tudo, comprovar limpeza e saúde.

### 7.2 Guardas obrigatórias

Escopo allowlisted de projeto/Compose/labels; recusar dependências externas, volume compartilhado, inventário inesperado, ambiente diferente de `poc`, plano expirado/adulterado, ausência de confirmação forte, backups ainda no volume e modificações posteriores ao preview. Preservar `.env`, Git, código-fonte, `workspace/notebooks`, arquivos pessoais e backups externos. Não alterar produção. Registrar `plan_id`, status, etapas, contagem antes/depois, hashes e falha parcial; mecanismo de recuperação após falha.

### 7.3 Testes de reset

Executar em stack isolada: povoar banco, MLflow, RustFS, fila e proposta; gerar preview sem alteração de hashes; rodar `reset-data/empty`; re-seedar e testar `factory-reset/demo-ready`; comprovar via SQL/SDK/S3/HTTP que não restaram runs, propostas ou binários anteriores; executar de novo jornada A+B após reconstrução. **Não rodar reset da stack principal**, mesmo que o usuário tenha pedido a funcionalidade.

## 8. Evolução de notebooks 03, 04, 06 e 07

- **03 Dados:** dataframe completo com tipos, dimensões, amostra, distribuição, nulos, datas, split temporal sem vazamento, snapshot/hash; tabelas e gráficos legíveis com séries/valores identificáveis.
- **04 Modelo individual:** seletor validado de snapshot, `model_key`, algoritmo e hiperparâmetros; baseline, fit/avaliação, run link, métricas, artefato+checksum, versão nova (candidata) e teste de reload. Prevenir re-run acidental duplicando versão sem identificação de tentativa.
- **06 Comparação:** comparação por mesmo snapshot/janela/coorte, métricas MAE/RMSE/(sMAPE quando disponível), tempo, tratamento de série curta e fallback; registrar critérios de escolha, sem promover automaticamente.
- **07 Governança:** filtrar versões, verificar proveniência/assinatura e apresentar métricas; aprovar/promover **somente com identidade autorizada, versão selecionada, justificativa e ação opt-in**; auditar no PostgreSQL e conferir alias no Registry; testar revogação/rollback e falha fechada em stack isolada.

## 9. Organização de MLflow e de 500+ modelos

- Um MLflow compartilhado por ambiente lógico; não um MLflow por modelo.
- Experimentos por **domínio ou campanha**, sem criar 500 experimentos arbitrários. `run_id` por tentativa e `registered_model_name`/`model_key` por identidade estável. Uma identidade pode possuir várias versões.
- Convenção recomendada (compatível com nomes legados via mapeamento): `hi.<dominio>.<campus>.<curso>.<periodo>`, evitando mudanças de nomes já usados sem migração documentada.
- Tags indexáveis: `solution_id`, `environment`, `domain`, `cycle_code`, `snapshot_id`, `model_key`, `training_campaign_id`, `code_version`, `config_hash`; `run_id` e `model_version` são nativos e devem ser recuperáveis sem duplicação ambígua.
- Alias de produção (`champion`) só após aprovação explícita; `candidate` não autoriza deployment. Registro não equivale a deploy.
- Workbench é ambiente de cientista, jobs treinam, Registry organiza versões, serviço de inferência serve modelos sob capacidade medida. Documentar caching, concorrência, limites de memória e critérios para serviços dedicados versus compartilhados.

## 10. README: reorganização para quem precisa demonstrar a arquitetura

O README deve começar pela **prova de arquitetura**, não pelo inventário de ferramentas. Estrutura obrigatória:

1. Objetivo, escopo DEMO e correspondência C2/C3 local↔GCP (Jupyter↔Workbench; RustFS↔Object Storage; PostgreSQL local↔Cloud SQL/PostgreSQL; Compose↔serviços Kubernetes); sem prometer equivalência de HA/custo/rede.
2. Diagrama de fluxo `SQL→Jupyter→MLflow/RustFS→inferência→Postgres→API` e distinção entre notebook 01 legado e nova geração via API.
3. Matriz de serviços, endpoints/portas, responsabilidade, persistência e autenticação, sem credenciais expostas.
4. Setup Windows/Linux, `.env`, `init`, `start`, `status`, `stop`, `rebuild` sem perda de dados; erros usuais e verificações.
5. **Roteiro de demonstração de 15–20 etapas**: 00 → 03 → 04/01 → MLflow → RustFS → 02 modo geração → API → banco → 08 lineage; outputs e critérios esperados.
6. Campanhas 05 e organização de 500 modelos; números separados entre identidades, treinos, versões e instâncias em serving.
7. Governança 06/07, reset 09 com operação externa e confirmação, relatórios e recuperação.
8. Contrato de Planilha Turmas com payload JSON de exemplo explicitamente provisório, Swagger e validação V4.4 por regra.
9. Evidências PASS/PARTIAL/NOT_EXECUTED e troubleshooting; links para documentação detalhada.

Também atualizar `notebooks/README.md`, `docs/operations/INFERENCE_NOTEBOOK.md`, `RESET_POC.md`, `MLFLOW_MODEL_ORGANIZATION.md`, `docs/architecture/LINEAGE.md`, `FUNCTIONAL_COVERAGE.md` e as ADRs afetadas. **Não repetir documentação histórica de Kubernetes como se ainda fosse o runtime da POC.**

## 11. Plano de implementação Codex — ordem e checkpoints

| Fase | Entrega verificável | Gate |
|---|---|---|
| A | Inventário HEAD, diff V1.1, matriz V3/V4.4, falhas atuais e riscos de dados | Relatório antes de editar |
| B | API/worker de geração com persistência e idempotência; contrato e tests | POST→job/status→GET→SQL/S3 PASS |
| C | Notebook 02 em dois modos com evidências reais | Kernel novo, chamada HTTP real, nova proposta e validação |
| D | Campanhas persistentes + notebook 05 | 30 modelos reais, restart/retry e estados PASS |
| E | Lineage UI/notebook 08 e tags completas | Busca bidirecional N:N, links, hashes, casos negativos |
| F | Notebooks 03/04/06/07 e catálogo completo | Read-only e opt-in executados em stack isolada |
| G | Notebook 09 + controlador de reset | preview, reset-data, factory-reset e reconstrução isolada PASS |
| H | README/documentação/contratos/ADRs | Roteiro utilizável e sem contradições |
| I | CI, testes integrados, benchmark, preservação | Relatório assinado por commit, evidências e limitações |

**Regra de segurança:** antes de qualquer migração, executar backup/verificação em instância isolada. No ambiente principal, não apagar volumes/experimentos/propostas; nenhuma fase autoriza reset ali. Sempre rodar `dev/generate_compose.py --check` se alterar `compose.yaml`.

## 12. Critérios de aceite V2 (não negociáveis)

| ID | Prova exigida | Condição de PASS |
|---|---|---|
| V2-01 | Jornada 01 preservada | Kernel novo, SQL→treino→Registry→RustFS→proposta→API; relatório íntegro |
| V2-02 | API gera proposta | POST real cria nova geração `DRAFT`, persiste e GET devolve contrato íntegro |
| V2-03 | Orquestração e idempotência | Job/status ou ADR de limitação; chave igual não duplica, payload diferente rejeita |
| V2-04 | Notebook 02 operacional | Modo A + modo B reais, sem acessar banco diretamente para escrever |
| V2-05 | Contrato e V4.4 | Schema OpenAPI/Pydantic, validações por RGN/RF/US; lacunas NOT_EVALUATED |
| V2-06 | MLflow/RustFS | Runs/versões, modelo recuperado com SHA-256 igual, sem fallback local |
| V2-07 | Linhagem cruzada | proposta→run/modelo/snapshot/artefato e busca reversa; N:N por linha |
| V2-08 | Notebook 05 funcional | Submeter campanha, consultar progresso, retomar, cancelar/retry com estado persistente |
| V2-09 | Campanha 30 real | 30 treinos reais comprovados individualmente; sem promoção automática |
| V2-10 | Campanha 500 | **Somente PASS se 500 treinamentos reais ocorrerem**; senão NOT_EXECUTED, distinto do catálogo de 500 identidades |
| V2-11 | Governança | Seleção de candidato, aprovação opt-in, auditoria e rollback isolado |
| V2-12 | Reset | Preview imutável, reset-data/empty e factory/demo-ready somente em stack descartável; prova pós-rebuild |
| V2-13 | Proteção do projeto | SHA256 de arquivos protegidos, runs/versões/propostas anteriores preservados |
| V2-14 | Notebooks 00–09 | Cada notebook com objetivo, parâmetros, evidência e execução real aplicável |
| V2-15 | CI | Workflow limpo `success`, build, migração, API, testes e artefatos sem segredos |
| V2-16 | README completo | Desenvolvedor novo reproduz jornadas A/B e encontra todos os IDs/links |

**Proibido:** chamar um teste de 500 identidades de “500 modelos treinados”; chamar GET de proposta de “geração via inferência”; chamar notebook de uma célula de “pipeline de campanhas”; chamar `Run All` do reset de “factory reset executado”; chamar `NOT_EVALUATED` de homologação funcional.

## 13. Evidências e formato de entrega final do Codex

Gerar em `artifacts/reports/v2/`:

- `inventory-before.json`, `implementation-diff.md`, `acceptance-v2.json`, `acceptance-v2.md`;
- notebook 01 e 02 executados, request/response HTTP sanitizados, OpenAPI/schema, execução SQL de verificação, referências do Registry e digests S3;
- `training-campaign-30.json`, `training-campaign-500.json` **somente se executada**, métricas CPU/RAM/tempo/erros e logs de restart/retry;
- `lineage-cross-system.json`, `lineage-negative-tests.json`, `reset-isolated-proof.json`;
- `ci-result.json`, `preservation-after.json`, suíte JUnit e testes de contrato.

Todo relatório deve conter `timestamp_utc`, `git_commit`, `environment`, `test_id`, `status`, `source_type`, IDs e links reais, evidence path, cenário e limitações. Não versionar segredos, tokens, dumps de dados pessoais ou binários de modelos inadvertidamente. Se a execução real não ocorrer, usar `NOT_EXECUTED` e explicar o bloqueio, sem construir relatórios fictícios.

### Entrega de código

- Implementar alterações na `development` (ou branch de trabalho com PR para `development`, conforme fluxo existente). Não fazer merge em `staging` ou `main` sem autorização.
- Descrever cada mudança e qual problema V1.1 resolveu; manter compatibilidade e migrações aditivas.
- Informar exatamente quais arquivos mudaram, quais notebooks executaram, resultados dos testes, commit/PR e pendências não demonstradas.
- Ao final, apresentar o **roteiro real de demonstração da POC** com links dos endpoints do ambiente e os comandos para iniciar a stack. Não declarar que o usuário já aprovou o contrato acadêmico.

---

## 14. Resumo do comportamento esperado

O cientista entra no Jupyter, identifica e prepara um snapshot, treina um ou mais modelos, vê as métricas no MLflow e o binário no RustFS. Em seguida, abre o **notebook 02**, solicita uma **nova Planilha Turmas por meio da API**, acompanha a geração, visualiza o contrato exato recebido pela aplicação e comprova que a mesma proposta foi gravada no PostgreSQL. A partir do `proposal_id`, navega intuitivamente até cada snapshot, run, versão e binário. O **notebook 05** gerencia campanhas reais e o **09** permite planejar e auditar um reset total seguro, executado por controlador externo e comprovado somente em ambiente descartável. A POC deve ser reproduzível, documentada e verificável com evidências — sem confundir simulação, implementação, teste e homologação.
