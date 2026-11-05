> Estado vigente (05/11/2026): jornada V4 em Docker Compose, treinamento no Workbench, experimento por campanha e reset seletivo preservando a origem SQL. Consulte o [índice V4](docs/README.md) e a [ADR 012](docs/adr/012-workbench-academic-v4.md). O texto abaixo preserva a baseline histórica e seus contratos; não é roteiro de operação atual.

# SPEC — PUCPR Horários Inteligentes | baseline e evolução

As instruções de correção V4 foram fornecidas localmente em `dev/`, pasta não
publicada. A implementação e as decisões atuais estão documentadas no
[README](README.md), no [runbook V4](docs/operations/POC_V4_MANUAL_RUNBOOK.md)
e nas evidências de `artifacts/reports`. Seções históricas abaixo permanecem
para rastreio do contrato original, sem reativar topologias substituídas.

**Versão:** 1.0 (baseline de implementação)  
**Estado:** proposta técnica da PoC; não equivale a implantação concluída nem à homologação do C3  
**Idioma:** pt-BR  
**Público:** Codex, arquitetura de soluções, engenharia de dados, MLOps, plataforma e sustentação.

## 1. Objetivo e limites

Implementar uma PoC local, reprodutível e containerizada, simulando o C3 da PUCPR: JupyterLab para treinamento supervisionado de pelo menos **30 modelos de séries temporais**, MLflow para Tracking/Registry, RustFS como armazenamento de objetos S3, PostgreSQL para metadados e planejamento, FastAPI para inferência, RabbitMQ/Celery para jobs assíncronos e dashboard operacional próprio HTML/CSS/JS com logs JSONL. Toda execução da solução ocorre em **pods Kubernetes K3s gerenciados pelo Rancher Desktop**. O host mantém somente Rancher Desktop, virtualização/WSL2, kubectl, Helm, runtime de build, scripts e navegador.

**Fora do escopo:** dados reais da PUCPR; Entra ID; Apigee; conectividade Azure↔GCP; execução em GKE; solver de ensalamento real; ranking docente definitivo; publicação em sistemas acadêmicos; treinamentos automáticos sem supervisão; alta disponibilidade de bancos. Dados serão **100% sintéticos** e não serão confundidos com históricos institucionais.

**Rastreabilidade:** cada sugestão deve referenciar ciclo, snapshot imutável, versão aprovada do modelo, execução e previsão; alterações humanas, caso simuladas, não devem sobrescrever a sugestão original.

## 2. Decisões de arquitetura e topologia

| Domínio | Namespace | Objetos | Persistência |
|---|---|---|---|
| Treinamento (simula Workbench externo) | `training` | Jupyter `Deployment` 1 réplica, `Service`, `PVC`; `Job` sob demanda | workspace PVC; snapshots no RustFS |
| MLOps | `mlops` | MLflow `Deployment`/`Service`; `monitoramento` `Deployment`/`Service` contínuo readonly | metadados `mlflow_db`, artefatos RustFS |
| Inferência | `ai-service` | `inference` `Deployment`/`Service` carrega modelos do S3; `api` FastAPI expõe Serviços Inteligentes; `worker` Celery processa lotes | `planejamento_db`; cache de modelos em memória no inference |
| Dados | `data` | PostgreSQL `StatefulSet`, RustFS `StatefulSet`/chart validado, RabbitMQ `StatefulSet`; Services, PVCs, Jobs | PVCs com retenção |
| Operação | `operations` | UI + backend, collector `Deployment`, PVC RWX compartilhado ou sidecar/único pod | JSONL no PVC |

**Nota crítica de PVC:** K3s local-path geralmente é RWO, não presumir RWX. Preferir **dashboard backend e collector no mesmo pod com um PVC RWO** ou coletor que grave via API interna. Não configurar dois pods distintos montando o mesmo RWO em nós diferentes. A PoC não deve montar diretórios `hostPath` de dados manualmente.

**Revisão solicitada pelo usuário (ADR-006):** separar a API pública do runtime de modelos.
API/worker chamam `inference.ai-service.svc.cluster.local:8001` com token interno.
O runtime valida aprovação/Registry e carrega artefatos do RustFS sob demanda; a API
não carrega modelos localmente. Monitoramento passa a pod contínuo somente leitura,
sem disparar treinos. Scripts `deployment/scripts/namespaces.ps1`/`.sh` e guia
`docs/commands/NAMESPACE_DEPLOY.md` cobrem configuração, build, deploy e operação por namespace.

**DNS interno ilustrativo:** `postgres.data.svc.cluster.local:5432`, `rustfs.data.svc.cluster.local:9000`, `rabbitmq.data.svc.cluster.local:5672`, `mlflow.mlops.svc.cluster.local:5000`, `api.ai-service.svc.cluster.local:8000`. Confirmar nomes reais produzidos pelos Helm charts. Tráfego REST por HTTP interno na PoC; credenciais por Secrets; acesso externo somente por `kubectl port-forward` em loopback.

**Síncrono:** notebook→MLflow HTTP; API→PostgreSQL SQL; API→MLflow metadata; predição unitária. **Assíncrono:** FastAPI→RabbitMQ→Celery para previsão em lote; disparos explícitos de `Job` para treinamento. Uma chamada síncrona dentro de um worker não transforma o job do usuário em síncrono.

## 3. Organização obrigatória de repositório

```text
pucpr-mlops-poc/
├── deployment/
│   ├── docker/{jupyter,mlflow,api,worker,monitor,dashboard}/
│   ├── helm/{platform,training,mlops,ai-service,operations}/
│   ├── kubernetes/{namespaces,networkpolicies,rbac,jobs}/
│   ├── values/{local,gke-example}/
│   └── scripts/{setup.ps1,setup.sh,deploy.ps1,deploy.sh,run.ps1,run.sh,common.ps1,common.sh}
├── config/{app.yaml,training.yaml,models.yaml,inference.yaml,logging.yaml,dashboard.yaml,environment.yml}
├── data/{raw,bronze,silver,gold,snapshots,samples}/
├── artifacts/{exports,reports}/
├── notebooks/{00_environment_validation.ipynb,01_exploration.ipynb,02_features.ipynb,03_training.ipynb,04_evaluation.ipynb,05_registry.ipynb,06_inference.ipynb,07_retraining.ipynb}
├── src/{common,data,training,inference,api,workers,mlops,monitoring,persistence,dashboard}/
├── tests/{unit,integration,e2e}/
├── docs/{installation,architecture,operations,commands,troubleshooting,adr}/
├── sql/{bootstrap,ddl,queries,seed}/
├── .env.example
├── .gitignore
├── pyproject.toml
├── Makefile
├── README.md
└── spec.md
```

Configuração YAML versionada, Secrets via `.env` gerado localmente e Secret Kubernetes, jamais senha em notebook ou repositório. Dockerfile com imagens fixadas por tag/digest após verificação. RustFS é **proposta** S3: validar endpoints, compatibilidade MLflow/boto3 e chart antes do deploy; se inviável, documentar bloqueio e opção OSS aprovada, sem troca silenciosa.

## 4. Contrato dos três pipelines

### 4.1 `setup.ps1` / `setup.sh` — host/plataforma

`check`, `install`, `validate`, `help`. Windows: verificar arquitetura 64-bit, WSL2, virtualização, Rancher Desktop, K3s habilitado, Moby, kubectl, Helm e contexto `rancher-desktop`. Permitir instalação assistida via gerenciador oficial onde suportada, mas **não** instalar plataforma silenciosamente nem assumir privilégios administrativos. `install` deve registrar operações que exigem reinício do Windows, instruir e sair com código apropriado. Linux: verificar requisitos da distribuição e virtualização. `validate` testa `kubectl cluster-info`, nodes Ready, `helm version`, StorageClass, acesso a registry, memória e espaço em disco; exibe checklist PASS/FAIL.

### 4.2 `deploy.ps1` / `deploy.sh` — ciclo de entrega

`preflight`, `build`, `install`, `upgrade`, `verify`, `status`, `rollback`, `uninstall`, `purge`. Rejeitar qualquer contexto diferente de `rancher-desktop` por padrão. O deploy **não depende de Python instalado no host**. Build OCI com Moby e validação de que imagem fica acessível ao K3s. Helm upgrades idempotentes, `--wait`/timeouts, `kubectl rollout status`, probes e checkpoints. Ordem: namespaces → secrets/configmaps → PVC → PostgreSQL → bootstrap DB → Alembic → RustFS → buckets → RabbitMQ → MLflow → Jupyter → FastAPI → Celery → monitor → dashboard/collector → smoke tests. `purge` exige confirmação explícita e texto digitado; nunca apagar outros namespaces.

### 4.3 `run.ps1` / `run.sh` — operação após build

`start`, `stop`, `restart <serviço>`, `status`, `urls`, `forward`, `logs <serviço> [--tail N|--follow|--since]`, `diagnose`, `seed`, `train`, `evaluate`, `promote`, `predict`, `monitor`, `retrain`, `test`, `e2e`, `backup`, `restore`. `start` não reinstala Helm: verifica cluster, restabelece réplicas previamente pausadas, aguarda readiness e exibe URLs. `stop` é gracioso e preserva PVC. Port-forwards controlados por PID com log e arquivo de controle do script (infra de acesso no host, nenhum serviço de aplicação fora do K8s). `logs` resolve serviços/namespaces e pode também acessar logs consolidados pela API. `diagnose` captura eventos, PVC, pods, deployments, StatefulSets, jobs, logs e status de charts, com sanitização de segredos. Backup/restore por Kubernetes Job e objetos S3; documentar RPO/RTO como não garantidos nesta PoC.

### 4.4 Guia exato de primeira utilização

```powershell
.\deployment\scripts\setup.ps1 check
.\deployment\scripts\setup.ps1 install
# concluir ações manuais/restart necessários
.\deployment\scripts\setup.ps1 validate
.\deployment\scripts\deploy.ps1 build
.\deployment\scripts\deploy.ps1 install
.\deployment\scripts\deploy.ps1 verify
.\deployment\scripts\run.ps1 start
.\deployment\scripts\run.ps1 forward all
.\deployment\scripts\run.ps1 urls
.\deployment\scripts\run.ps1 seed
.\deployment\scripts\run.ps1 train
.\deployment\scripts\run.ps1 e2e
```

Bash deve manter semântica equivalente. Portas padrão no loopback: dashboard `8088`, Jupyter `8888`, MLflow `5000`, API `8000`, RabbitMQ UI `15672`, console RustFS se suportado `9001`; se porta ocupada, falhar com mensagem ou aceitar override.

## 5. Contrato Jupyter pronto para uso

Imagem com Conda/Mamba, Python 3.12 ou versão compatível testada, JupyterLab, kernel registrado, `pandas`, `numpy`, `pyarrow`, `scikit-learn`, `statsmodels`, `matplotlib`, `mlflow`, `boto3`, `sqlalchemy`, `psycopg`, `pydantic`, `httpx`, `pytest`. `environment.yml` fixa versões depois de teste. Notebook `00_environment_validation.ipynb` testa kernel, PostgreSQL somente leitura, MLflow, RustFS bucket, dados Gold, API e permissões; exibe resultados claros PASS/FAIL sem imprimir credenciais. Variáveis `MLFLOW_TRACKING_URI`, `MLFLOW_S3_ENDPOINT_URL`, S3 bucket, DB readonly URI e API URI vêm de ConfigMaps/Secrets. Código reutilizável em `src/`, não duplicado nos notebooks. Workspace em PVC, token Jupyter em Secret; sem acesso público.

## 6. Dados, séries temporais e regras da PoC

Gerar 30 chaves `campus + curso + período` (3 campi × 5 cursos × 2 períodos), 12 semestres históricos por série (configurável), tendências, sazonalidade, ruído determinístico, lacunas e cursos novos. Persistir Parquet por camada e manifesto de snapshot com checksum, schema_version e as_of_date. **Não vazar períodos futuros no treino.** Pipeline Raw→Bronze→Silver→Gold versionado. Camada Gold com séries por campus, curso, período, ano, semestre e regulares/dependência/eletiva. Validação: chaves únicas, contagens ≥0, ordenação temporal, integridade referencial, cobertura histórica. Cada modelo compara baseline sazonal, regressão com lags e HistGradientBoosting/RandomForest conforme amostra; time-series backtesting, MAE/RMSE/sMAPE; fallback explícito para pouco histórico, sem inventar dados. Treinar em Job explícito, no máximo 2 concorrências inicialmente, medir memória e duração.

Model Registry por chave estável, artefatos RustFS, tags MLflow com `snapshot_id`, `model_key`, `code_version`, `config_hash`. Treinar não promove automaticamente. Aprovação por operador técnico com justificativa gera alias `champion` e registro auditável em `model_deployments`; rollback controlado. Inferência unitária síncrona e batch assíncrona via RabbitMQ/Celery; estado durável em `planejamento_db`; Celery não deve tomar RabbitMQ como armazenamento definitivo de resultados. Sugestões são ofertas projetadas **não** matrículas reais, e a regra de distribuição por disciplina é sintética e documentada.

## 7. PostgreSQL — provisioning explícito

**Workload:** `StatefulSet/postgres` no namespace `data`, 1 réplica, `Service` ClusterIP e PVC (`ReadWriteOnce`), probes, requests/limits, backup lógico; `Job/db-bootstrap` idempotente cria duas databases reais, usuários e permissões distintos. Conceder ao usuário de aplicativo apenas DML no schema `planning` e ao usuário de migração DDL; não usar superuser na API. `mlflow_db` com schema gerenciado pelo MLflow; `planejamento_db` com DDL abaixo, implementada como migrations Alembic revisáveis (o SQL é contrato canônico, não executado paralelamente às migrations). Não codificar senha. Triggers de imutabilidade e privilégios, TLS quando aplicável e documentação de diferenças locais/GKE.

## 8. DDL CANÔNICA — `planejamento_db`

A sequência de criação, constraints, tipos, relacionamentos, índices e triggers é base mandatória. Ajustes de convenção feitos pelo Codex exigem ADR e atualização simultânea do catálogo na seção 9.

```sql
-- Database planejamento_db; executar com role de migração
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS planning;
SET search_path TO planning, public;

CREATE TABLE IF NOT EXISTS planning.campuses (
    id uuid PRIMARY KEY,
    code varchar(20) NOT NULL UNIQUE,
    name varchar(120) NOT NULL,
    active boolean NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS planning.courses (
    id uuid PRIMARY KEY,
    campus_id uuid NOT NULL REFERENCES planning.campuses(id),
    code varchar(30) NOT NULL,
    name varchar(180) NOT NULL,
    active boolean NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS planning.academic_periods (
    id uuid PRIMARY KEY,
    course_id uuid NOT NULL REFERENCES planning.courses(id),
    period_number smallint NOT NULL CHECK (period_number BETWEEN 1 AND 20),
    active boolean NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS planning.disciplines (
    id uuid PRIMARY KEY,
    course_id uuid NOT NULL REFERENCES planning.courses(id),
    code varchar(40) NOT NULL,
    name varchar(200) NOT NULL,
    credits numeric(6,2) NOT NULL CHECK (credits >= 0),
    modulation_limit integer NOT NULL CHECK (modulation_limit > 0),
    active boolean NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS planning.period_disciplines (
    period_id uuid NOT NULL REFERENCES planning.academic_periods(id),
    discipline_id uuid NOT NULL REFERENCES planning.disciplines(id),
    mandatory boolean NOT NULL DEFAULT TRUE,
    PRIMARY KEY (period_id, discipline_id)
);

CREATE TABLE IF NOT EXISTS planning.academic_cycles (
    id uuid PRIMARY KEY,
    cycle_code varchar(12) NOT NULL UNIQUE,
    target_year smallint NOT NULL,
    target_semester smallint NOT NULL CHECK (target_semester IN (1,2)),
    status varchar(24) NOT NULL,
    starts_at timestamptz,
    ends_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (target_semester IN (1,2)), CHECK (status IN ('DRAFT','READY','RUNNING','REVIEW','APPROVED','CLOSED'))
);

CREATE TABLE IF NOT EXISTS planning.dataset_snapshots (
    id uuid PRIMARY KEY,
    snapshot_key varchar(100) NOT NULL UNIQUE,
    cycle_id uuid REFERENCES planning.academic_cycles(id),
    layer varchar(12) NOT NULL,
    bucket varchar(120) NOT NULL,
    object_prefix text NOT NULL,
    schema_version varchar(30) NOT NULL,
    sha256 char(64) NOT NULL,
    row_count bigint NOT NULL CHECK (row_count >= 0),
    source_reference varchar(120) NOT NULL,
    as_of_date date NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    sealed_at timestamptz,
    CHECK (layer IN ('RAW','BRONZE','SILVER','GOLD'))
);

CREATE TABLE IF NOT EXISTS planning.historical_enrollments (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    campus_id uuid NOT NULL REFERENCES planning.campuses(id),
    course_id uuid NOT NULL REFERENCES planning.courses(id),
    period_id uuid NOT NULL REFERENCES planning.academic_periods(id),
    reference_year smallint NOT NULL,
    reference_semester smallint NOT NULL CHECK (reference_semester IN (1,2)),
    regular_students integer NOT NULL CHECK (regular_students >= 0),
    dependency_students integer NOT NULL CHECK (dependency_students >= 0),
    elective_students integer NOT NULL CHECK (elective_students >= 0),
    snapshot_id uuid NOT NULL REFERENCES planning.dataset_snapshots(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK (reference_semester IN (1,2))
);

CREATE TABLE IF NOT EXISTS planning.model_catalog (
    id uuid PRIMARY KEY,
    model_key varchar(160) NOT NULL UNIQUE,
    campus_id uuid NOT NULL REFERENCES planning.campuses(id),
    course_id uuid NOT NULL REFERENCES planning.courses(id),
    period_id uuid NOT NULL REFERENCES planning.academic_periods(id),
    mlflow_registered_name varchar(240) NOT NULL,
    active boolean NOT NULL DEFAULT TRUE,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS planning.training_executions (
    id uuid PRIMARY KEY,
    model_id uuid NOT NULL REFERENCES planning.model_catalog(id),
    snapshot_id uuid NOT NULL REFERENCES planning.dataset_snapshots(id),
    mlflow_run_id varchar(100) UNIQUE,
    algorithm varchar(100) NOT NULL,
    code_version varchar(80) NOT NULL,
    config_hash char(64) NOT NULL,
    status varchar(24) NOT NULL,
    mae numeric(18,6),
    rmse numeric(18,6),
    smape numeric(12,6),
    duration_ms bigint,
    error_message text,
    started_at timestamptz,
    finished_at timestamptz
);

CREATE TABLE IF NOT EXISTS planning.model_deployments (
    id uuid PRIMARY KEY,
    model_id uuid NOT NULL REFERENCES planning.model_catalog(id),
    registered_version varchar(40) NOT NULL,
    artifact_uri text NOT NULL,
    alias varchar(40) NOT NULL,
    status varchar(20) NOT NULL,
    approved_by varchar(120) NOT NULL,
    justification text NOT NULL,
    approved_at timestamptz NOT NULL DEFAULT now(),
    revoked_at timestamptz,
    CHECK (status IN ('APPROVED','REVOKED'))
);

CREATE TABLE IF NOT EXISTS planning.prediction_jobs (
    id uuid PRIMARY KEY,
    cycle_id uuid NOT NULL REFERENCES planning.academic_cycles(id),
    snapshot_id uuid NOT NULL REFERENCES planning.dataset_snapshots(id),
    idempotency_key varchar(160) NOT NULL UNIQUE,
    correlation_id varchar(120) NOT NULL,
    status varchar(24) NOT NULL,
    requested_by varchar(120) NOT NULL,
    requested_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    finished_at timestamptz,
    total_models integer NOT NULL DEFAULT 0,
    completed_models integer NOT NULL DEFAULT 0,
    failed_models integer NOT NULL DEFAULT 0,
    error_summary text,
    CHECK (status IN ('PENDING','RUNNING','COMPLETED','PARTIAL_SUCCESS','FAILED'))
);

CREATE TABLE IF NOT EXISTS planning.predictions (
    id uuid PRIMARY KEY,
    job_id uuid NOT NULL REFERENCES planning.prediction_jobs(id),
    model_id uuid NOT NULL REFERENCES planning.model_catalog(id),
    deployment_id uuid NOT NULL REFERENCES planning.model_deployments(id),
    cycle_id uuid NOT NULL REFERENCES planning.academic_cycles(id),
    snapshot_id uuid NOT NULL REFERENCES planning.dataset_snapshots(id),
    campus_id uuid NOT NULL REFERENCES planning.campuses(id),
    course_id uuid NOT NULL REFERENCES planning.courses(id),
    period_id uuid NOT NULL REFERENCES planning.academic_periods(id),
    forecast_students integer NOT NULL CHECK (forecast_students >= 0),
    forecast_raw numeric(18,6) NOT NULL,
    lower_bound numeric(18,6),
    upper_bound numeric(18,6),
    is_fallback boolean NOT NULL,
    predicted_at timestamptz NOT NULL DEFAULT now(),
    CHECK (lower_bound IS NULL OR upper_bound IS NULL OR lower_bound <= upper_bound)
);

CREATE TABLE IF NOT EXISTS planning.offer_suggestions (
    id uuid PRIMARY KEY,
    prediction_id uuid NOT NULL REFERENCES planning.predictions(id),
    cycle_id uuid NOT NULL REFERENCES planning.academic_cycles(id),
    discipline_id uuid NOT NULL REFERENCES planning.disciplines(id),
    estimated_regular integer NOT NULL CHECK (estimated_regular >= 0),
    estimated_dependency integer NOT NULL CHECK (estimated_dependency >= 0),
    estimated_elective integer NOT NULL CHECK (estimated_elective >= 0),
    estimated_total integer NOT NULL CHECK (estimated_total >= 0),
    suggested_groups integer NOT NULL CHECK (suggested_groups > 0),
    status varchar(24) NOT NULL,
    generated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (estimated_total = estimated_regular + estimated_dependency + estimated_elective), CHECK (status IN ('SUGGESTED','EDITED','APPROVED','REJECTED'))
);

CREATE TABLE IF NOT EXISTS planning.model_quality_evaluations (
    id uuid PRIMARY KEY,
    model_id uuid NOT NULL REFERENCES planning.model_catalog(id),
    deployment_id uuid REFERENCES planning.model_deployments(id),
    cycle_id uuid NOT NULL REFERENCES planning.academic_cycles(id),
    actual_students integer NOT NULL CHECK (actual_students >= 0),
    predicted_students integer NOT NULL CHECK (predicted_students >= 0),
    absolute_error numeric(18,6) NOT NULL CHECK (absolute_error >= 0),
    quality_status varchar(20) NOT NULL,
    evaluated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS planning.audit_events (
    id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    actor_type varchar(20) NOT NULL,
    actor_id varchar(120) NOT NULL,
    event_type varchar(100) NOT NULL,
    entity_type varchar(80) NOT NULL,
    entity_id varchar(120) NOT NULL,
    correlation_id varchar(120) NOT NULL,
    previous_value jsonb,
    new_value jsonb,
    reason text
);

CREATE UNIQUE INDEX uq_course_campus_code ON courses(campus_id, code);
CREATE UNIQUE INDEX uq_period_course_number ON academic_periods(course_id,period_number);
CREATE UNIQUE INDEX uq_disc_course_code ON disciplines(course_id,code);
CREATE UNIQUE INDEX uq_history_series_time_snapshot ON historical_enrollments(campus_id,course_id,period_id,reference_year,reference_semester,snapshot_id);
CREATE UNIQUE INDEX uq_model_series ON model_catalog(campus_id,course_id,period_id);
CREATE UNIQUE INDEX uq_active_champion ON model_deployments(model_id) WHERE alias='champion' AND status='APPROVED';
CREATE UNIQUE INDEX uq_prediction_job_model ON predictions(job_id,model_id);
CREATE UNIQUE INDEX uq_offer_prediction_discipline ON offer_suggestions(prediction_id,discipline_id);
CREATE INDEX ix_prediction_cycle_course ON predictions(cycle_id,course_id,period_id);
CREATE INDEX ix_job_status_requested ON prediction_jobs(status,requested_at);
CREATE INDEX ix_audit_entity_time ON audit_events(entity_type,entity_id,occurred_at DESC);
CREATE INDEX ix_quality_model_time ON model_quality_evaluations(model_id,evaluated_at DESC);

-- Imutabilidade de auditoria: negar UPDATE e DELETE inclusive aos usuários da aplicação.
CREATE OR REPLACE FUNCTION planning.reject_audit_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'audit_events is append-only'; END; $$;
CREATE TRIGGER trg_audit_no_update BEFORE UPDATE OR DELETE ON planning.audit_events FOR EACH ROW EXECUTE FUNCTION planning.reject_audit_mutation();
-- Em produção: ownership da tabela e role de migração separadas; aplicação sem TRUNCATE/DDL.
```

### 8.1 Adendo de implementação — ADR-002

A migration 002 acrescenta as proteções abaixo sem remover tabelas ou colunas da baseline.

```sql
CREATE OR REPLACE FUNCTION planning.protect_snapshot() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF OLD.sealed_at IS NOT NULL THEN RAISE EXCEPTION 'sealed snapshot is immutable'; END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END; $$;
CREATE TRIGGER trg_snapshot_immutable BEFORE UPDATE OR DELETE ON planning.dataset_snapshots
FOR EACH ROW EXECUTE FUNCTION planning.protect_snapshot();

CREATE OR REPLACE FUNCTION planning.protect_history() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE sealed timestamptz;
BEGIN
  IF TG_OP IN ('UPDATE','DELETE') THEN
    IF EXISTS (SELECT 1 FROM planning.dataset_snapshots WHERE id=OLD.snapshot_id AND sealed_at IS NOT NULL) THEN
      RAISE EXCEPTION 'sealed history is immutable';
    END IF;
  END IF;
  IF TG_OP IN ('INSERT','UPDATE') THEN
    SELECT sealed_at INTO sealed FROM planning.dataset_snapshots WHERE id=NEW.snapshot_id FOR SHARE;
    IF sealed IS NOT NULL THEN RAISE EXCEPTION 'sealed history is immutable'; END IF;
    RETURN NEW;
  END IF;
  RETURN OLD;
END; $$;
CREATE TRIGGER trg_history_immutable BEFORE INSERT OR UPDATE OR DELETE ON planning.historical_enrollments
FOR EACH ROW EXECUTE FUNCTION planning.protect_history();

CREATE OR REPLACE FUNCTION planning.reject_prediction_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'original prediction/suggestion is immutable; record changes in audit'; END; $$;
CREATE TRIGGER trg_prediction_immutable BEFORE UPDATE OR DELETE ON planning.predictions
FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();
CREATE TRIGGER trg_offer_immutable BEFORE UPDATE OR DELETE ON planning.offer_suggestions
FOR EACH ROW EXECUTE FUNCTION planning.reject_prediction_mutation();

```

## 9. CATÁLOGO COMPLETO DE DADOS — derivado das DDLs

**Adendo ADR-002 ao catálogo:** dataset_snapshots torna-se imutável após sealed_at; historical_enrollments não aceita INSERT/UPDATE/DELETE para snapshot selado; predictions e offer_suggestions preservam o registro original (UPDATE/DELETE negados). Correções humanas futuras usam auditoria/registro separado. Nenhuma coluna foi adicionada ou removida. Triggers constam da seção 8.1.

**Legenda:** PK chave primária; FK chave estrangeira; NN não nulo; UQ único. A tabela não documenta campos inexistentes na DDL. Governança: dados de PoC são sintéticos; o modelo lógico poderá ser refinado quando os contratos oficiais da V4.4 e Prontidão forem homologados.

### 9.1 `planning.campuses`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `code` | `varchar(20)` | UQ NN | Código do campus |
| `name` | `varchar(120)` | NN | Nome |
| `active` | `boolean` | NN default true | Ativo |

### 9.7 `planning.courses`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `campus_id` | `uuid` | FK campuses NN | Campus |
| `code` | `varchar(30)` | NN | Código institucional sintético |
| `name` | `varchar(180)` | NN | Nome |
| `active` | `boolean` | NN default true | Ativo |

### 9.14 `planning.academic_periods`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `course_id` | `uuid` | FK courses NN | Curso |
| `period_number` | `smallint` | NN check 1..20 | Período da matriz |
| `active` | `boolean` | NN default true | Ativo |

### 9.20 `planning.disciplines`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `course_id` | `uuid` | FK courses NN | Curso |
| `code` | `varchar(40)` | NN | Código |
| `name` | `varchar(200)` | NN | Disciplina |
| `credits` | `numeric(6,2)` | NN >=0 | Créditos |
| `modulation_limit` | `integer` | NN >0 | Capacidade de modulação |
| `active` | `boolean` | NN default true | Ativo |

### 9.29 `planning.period_disciplines`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `period_id` | `uuid` | FK academic_periods NN | Período |
| `discipline_id` | `uuid` | FK disciplines NN | Disciplina |
| `mandatory` | `boolean` | NN default true | Obrigatória |

### 9.34 `planning.academic_cycles`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `cycle_code` | `varchar(12)` | UQ NN | Ex.: 2027-1 |
| `target_year` | `smallint` | NN | Ano alvo |
| `target_semester` | `smallint` | NN check 1/2 | Semestre alvo |
| `status` | `varchar(24)` | NN | DRAFT/READY/RUNNING/REVIEW/APPROVED/CLOSED |
| `starts_at` | `timestamptz` | nullable | Início parametrizado |
| `ends_at` | `timestamptz` | nullable | Fim parametrizado |
| `created_at` | `timestamptz` | NN default now | Criação |

### 9.44 `planning.dataset_snapshots`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `snapshot_key` | `varchar(100)` | UQ NN | Chave imutável |
| `cycle_id` | `uuid` | FK academic_cycles nullable | Ciclo |
| `layer` | `varchar(12)` | NN | RAW/BRONZE/SILVER/GOLD |
| `bucket` | `varchar(120)` | NN | Bucket S3 |
| `object_prefix` | `text` | NN | Prefixo objetos |
| `schema_version` | `varchar(30)` | NN | Versão do contrato |
| `sha256` | `char(64)` | NN | Checksum manifesto |
| `row_count` | `bigint` | NN >=0 | Linhas |
| `source_reference` | `varchar(120)` | NN | Origem sintética |
| `as_of_date` | `date` | NN | Data de referência |
| `created_at` | `timestamptz` | NN default now | Criação |
| `sealed_at` | `timestamptz` | nullable | Fechamento de snapshot |

### 9.59 `planning.historical_enrollments`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `bigint` | PK identity | Identificador |
| `campus_id` | `uuid` | FK campuses NN | Campus |
| `course_id` | `uuid` | FK courses NN | Curso |
| `period_id` | `uuid` | FK academic_periods NN | Período |
| `reference_year` | `smallint` | NN | Ano |
| `reference_semester` | `smallint` | NN check 1/2 | Semestre |
| `regular_students` | `integer` | NN >=0 | Alunos regulares |
| `dependency_students` | `integer` | NN >=0 | Dependências |
| `elective_students` | `integer` | NN >=0 | Eletivas |
| `snapshot_id` | `uuid` | FK dataset_snapshots NN | Snapshot |
| `created_at` | `timestamptz` | NN default now | Criação |

### 9.72 `planning.model_catalog`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `model_key` | `varchar(160)` | UQ NN | Chave campus/curso/período |
| `campus_id` | `uuid` | FK campuses NN | Campus |
| `course_id` | `uuid` | FK courses NN | Curso |
| `period_id` | `uuid` | FK academic_periods NN | Período |
| `mlflow_registered_name` | `varchar(240)` | NN | Nome do Registry |
| `active` | `boolean` | NN default true | Ativo |
| `created_at` | `timestamptz` | NN default now | Criação |

### 9.82 `planning.training_executions`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `model_id` | `uuid` | FK model_catalog NN | Modelo |
| `snapshot_id` | `uuid` | FK dataset_snapshots NN | Snapshot de entrada |
| `mlflow_run_id` | `varchar(100)` | UQ nullable | Run MLflow |
| `algorithm` | `varchar(100)` | NN | Algoritmo |
| `code_version` | `varchar(80)` | NN | Commit ou build |
| `config_hash` | `char(64)` | NN | Configuração |
| `status` | `varchar(24)` | NN | PENDING/RUNNING/SUCCEEDED/FAILED/FALLBACK |
| `mae` | `numeric(18,6)` | nullable | Erro absoluto médio |
| `rmse` | `numeric(18,6)` | nullable | Raiz erro quadrático |
| `smape` | `numeric(12,6)` | nullable | sMAPE |
| `duration_ms` | `bigint` | nullable | Duração |
| `error_message` | `text` | nullable | Falha sanitizada |
| `started_at` | `timestamptz` | nullable | Início |
| `finished_at` | `timestamptz` | nullable | Fim |

### 9.99 `planning.model_deployments`

**Finalidade:** Histórico de promoções/revogações dos modelos aprovados.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `model_id` | `uuid` | FK model_catalog NN | Modelo |
| `registered_version` | `varchar(40)` | NN | Versão MLflow |
| `artifact_uri` | `text` | NN | URI do artefato |
| `alias` | `varchar(40)` | NN | champion ou challenger |
| `status` | `varchar(20)` | NN | APPROVED/REVOKED |
| `approved_by` | `varchar(120)` | NN | Operador técnico |
| `justification` | `text` | NN | Motivo |
| `approved_at` | `timestamptz` | NN default now | Data aprovação |
| `revoked_at` | `timestamptz` | nullable | Revogação |

### 9.111 `planning.prediction_jobs`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `cycle_id` | `uuid` | FK academic_cycles NN | Ciclo |
| `snapshot_id` | `uuid` | FK dataset_snapshots NN | Snapshot |
| `idempotency_key` | `varchar(160)` | UQ NN | Deduplicação |
| `correlation_id` | `varchar(120)` | NN | Rastreabilidade |
| `status` | `varchar(24)` | NN | PENDING/RUNNING/COMPLETED/PARTIAL_SUCCESS/FAILED |
| `requested_by` | `varchar(120)` | NN | Autor técnico/sistema |
| `requested_at` | `timestamptz` | NN default now | Solicitação |
| `started_at` | `timestamptz` | nullable | Início |
| `finished_at` | `timestamptz` | nullable | Fim |
| `total_models` | `integer` | NN default 0 | Total esperado |
| `completed_models` | `integer` | NN default 0 | Total concluído |
| `failed_models` | `integer` | NN default 0 | Falhas |
| `error_summary` | `text` | nullable | Resumo sanitizado |

### 9.127 `planning.predictions`

**Finalidade:** Resultado bruto de uma execução de inferência, com linhagem completa.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `job_id` | `uuid` | FK prediction_jobs NN | Job |
| `model_id` | `uuid` | FK model_catalog NN | Modelo |
| `deployment_id` | `uuid` | FK model_deployments NN | Versão promovida |
| `cycle_id` | `uuid` | FK academic_cycles NN | Ciclo |
| `snapshot_id` | `uuid` | FK dataset_snapshots NN | Snapshot |
| `campus_id` | `uuid` | FK campuses NN | Campus |
| `course_id` | `uuid` | FK courses NN | Curso |
| `period_id` | `uuid` | FK academic_periods NN | Período |
| `forecast_students` | `integer` | NN >=0 | Previsão arredondada |
| `forecast_raw` | `numeric(18,6)` | NN | Previsão anterior às regras de domínio |
| `lower_bound` | `numeric(18,6)` | nullable | Intervalo inferior |
| `upper_bound` | `numeric(18,6)` | nullable | Intervalo superior |
| `is_fallback` | `boolean` | NN default false | Fallback |
| `predicted_at` | `timestamptz` | NN default now | Execução |

### 9.144 `planning.offer_suggestions`

**Finalidade:** Sugestões acadêmicas derivadas das previsões, ainda não aprovadas institucionalmente.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `prediction_id` | `uuid` | FK predictions NN | Previsão origem |
| `cycle_id` | `uuid` | FK academic_cycles NN | Ciclo |
| `discipline_id` | `uuid` | FK disciplines NN | Disciplina |
| `estimated_regular` | `integer` | NN >=0 | Regulares |
| `estimated_dependency` | `integer` | NN >=0 | Dependências |
| `estimated_elective` | `integer` | NN >=0 | Eletivas |
| `estimated_total` | `integer` | NN >=0 | Total |
| `suggested_groups` | `integer` | NN >0 | Grupos previstos |
| `status` | `varchar(24)` | NN | SUGGESTED/EDITED/APPROVED/REJECTED |
| `generated_at` | `timestamptz` | NN default now | Geração |

### 9.157 `planning.model_quality_evaluations`

**Finalidade:** Entidade de suporte ao pipeline sintético de previsão e rastreabilidade.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `uuid` | PK | Identificador |
| `model_id` | `uuid` | FK model_catalog NN | Modelo |
| `deployment_id` | `uuid` | FK model_deployments nullable | Versão |
| `cycle_id` | `uuid` | FK academic_cycles NN | Ciclo |
| `actual_students` | `integer` | NN >=0 | Real sintético |
| `predicted_students` | `integer` | NN >=0 | Previsto |
| `absolute_error` | `numeric(18,6)` | NN >=0 | Erro |
| `quality_status` | `varchar(20)` | NN | OK/WARNING/CRITICAL |
| `evaluated_at` | `timestamptz` | NN default now | Avaliação |

### 9.168 `planning.audit_events`

**Finalidade:** Trilha append-only de eventos de domínio e governança.

| Coluna | Tipo PostgreSQL | Restrições | Significado |
|---|---|---|---|
| `id` | `bigint` | PK identity | Identificador |
| `occurred_at` | `timestamptz` | NN default now | Data |
| `actor_type` | `varchar(20)` | NN | USER/SERVICE/JOB |
| `actor_id` | `varchar(120)` | NN | Autor |
| `event_type` | `varchar(100)` | NN | Evento |
| `entity_type` | `varchar(80)` | NN | Objeto |
| `entity_id` | `varchar(120)` | NN | ID objeto |
| `correlation_id` | `varchar(120)` | NN | Correlação |
| `previous_value` | `jsonb` | nullable | Estado anterior |
| `new_value` | `jsonb` | nullable | Estado posterior |
| `reason` | `text` | nullable | Justificativa |

## 10. SQL operacional e semântica de transações

**Exemplos que devem existir em `sql/queries/`:** consultar previsões por ciclo/modelo; sugestões com lineage; runs ainda sem champion; contagem jobs por status; última qualidade; chave idempotente; auditoria de promoção; validação de snapshots. Consultas de produção sempre parametrizadas, sem SQL de usuário concatenado. Uso dos dados por `read-only` no Jupyter quando possível. DDL no schema `planning`; nenhuma tabela do sistema de rastreamento MLflow deve ser criada manualmente no `mlflow_db`.

```sql
-- Sugestões com proveniência
SELECT c.cycle_code, mc.model_key, md.registered_version,
       ds.snapshot_key, p.forecast_students, os.estimated_total,
       os.status, p.predicted_at
FROM planning.offer_suggestions os
JOIN planning.predictions p ON p.id=os.prediction_id
JOIN planning.academic_cycles c ON c.id=os.cycle_id
JOIN planning.model_catalog mc ON mc.id=p.model_id
JOIN planning.model_deployments md ON md.id=p.deployment_id
JOIN planning.dataset_snapshots ds ON ds.id=p.snapshot_id
ORDER BY p.predicted_at DESC LIMIT 100;

-- Jobs e pendências
SELECT status, count(*) AS jobs, max(requested_at) AS ultimo
FROM planning.prediction_jobs GROUP BY status ORDER BY status;

-- 30 modelos previstos
SELECT count(*) AS modelos, count(*) FILTER (WHERE active) AS ativos
FROM planning.model_catalog;
```

**Transações:** API grava `prediction_jobs` antes de publicar a tarefa, empregando idempotency_key e padrão de recuperação para falha entre commit e publish (outbox recomendado se a PoC implementar garantia forte). Worker atualiza status e persiste previsões em transação, com `UNIQUE(job_id,model_id)`. Jobs `PARTIAL_SUCCESS` detalham falhas por modelo (recomenda-se tabela `prediction_job_items` caso implementado rastreamento granular); se adicionada, atualizar DDL/catálogo. Auditoria append-only: proteção de autorização, trigger, e sem TRUNCATE/ALTER pelo usuário da aplicação. `model_deployments` precisa garantir consistência de promoção entre MLflow alias e banco: tratar inconsistência como incidente recuperável, com reconciliação.

## 11. Dashboard de logs (sem Grafana)

**Frontend:** HTML/CSS/JS estático próprio, modo escuro, responsivo. **Backend:** FastAPI no namespace `operations`; **collector:** Kubernetes API `pods/log` por ServiceAccount com RBAC por namespace; persiste JSONL em PVC (recomendação: co-locar collector e backend no **mesmo pod** usando volume RWO, sem pressupor RWX). Backpressure, rotação, retenção (padrão 7 dias/limite 1 GB ajustável), checkpoints, deduplicação aproximada, normalização timestamp e redaction de secrets. Sem prometer exactly-once; stdout de pods apagados antes da coleta pode ser perdido. Não usar cluster-admin nem ler logs de outros namespaces.

**URL:** `localhost:8088` via port-forward seguro. **Abas:** Geral (pods/status), Logs (namespace, serviço, pod, severidade, intervalo, correlation_id, texto, follow/pause/export), Jobs, Modelos/MLflow, Conexões (DB/S3/RabbitMQ/API), Kubernetes (pods/PVCs/eventos). Atualização via SSE ou polling controlado. Login local token em Secret, RBAC backend somente leitura, sem terminal remoto nem endpoint de comandos arbitrários. API mínima: `/health`, `/ready`, `/api/health/services`, `/api/logs`, `/api/logs/stream`, `/api/k8s/resources`, `/api/jobs`, `/api/models`; validar paginação, filtros, limites de payload e autorização.

## 12. API Serviços Inteligentes — contratos mínimos

| Método | Rota | Semântica | Resposta |
|---|---|---|---|
| GET | `/health` | liveness | 200 |
| GET | `/ready` | readiness dependências críticas | 200/503 |
| GET | `/v1/models` | catálogo e champions | 200 |
| GET | `/v1/models/{model_key}` | versão e métricas | 200/404 |
| POST | `/v1/inference/predict` | uma série, síncrono | 200/422 |
| POST | `/v1/inference/batch` | cria job idempotente | 202 + job_id |
| GET | `/v1/jobs/{job_id}` | status | 200/404 |
| GET | `/v1/jobs/{job_id}/results` | pagina resultados | 200/404/409 |
| GET | `/v1/predictions` | filtros e paginação | 200 |
| GET | `/v1/monitoring/models` | qualidade | 200 |

Headers: `X-Correlation-ID` com validação, `Idempotency-Key` obrigatório no batch, autenticação por token dev no modo local com controles documentados (sem dados públicos reais). JSON schema Pydantic versionado, erros uniformes (`code`,`message`,`correlation_id`), timeout e limites por requisição. FastAPI não treina modelos. Model loader resolve alias aprovado, versão, artefato e schema de features; cache limitado com invalidação na promoção.

## 13. Critérios de aceite e roteiro de teste

- [ ] `setup` verifica Rancher/WSL2/K3s/Helm sem instalar aplicações no host.
- [ ] `deploy` instala 5 namespaces, StatefulSets e PVCs; all pods Ready.
- [ ] PostgreSQL contém duas databases distintas e roles mínimas.
- [ ] RustFS é acessado via S3 SDK por MLflow e Jupyter.
- [ ] Jupyter notebook 00 retorna PASS para todas as conexões.
- [ ] 30 séries sintéticas, snapshots imutáveis e catálogo de modelos correspondente.
- [ ] 30 treinamentos rastreáveis, com métricas ou fallback explicitado.
- [ ] Modelos candidatos não aparecem como champion sem ação de promoção.
- [ ] Predição unitária síncrona retorna versão/snapshot.
- [ ] Batch retorna 202, Celery processa e `planejamento_db` recebe previsões/sugestões.
- [ ] Duas chamadas com mesma chave idempotente não duplicam resultados.
- [ ] Dashboard coleta e filtra logs reais e os mantém após reinício do pod.
- [ ] `run logs`, `run diagnose`, `run backup/restore`, `run restart`, `run urls` têm exemplos reais e testes.
- [ ] Testes de PVC sobrevivem a recriação de pod e redeploy; `purge` exige confirmação.
- [ ] Evidências de execução e resultados PASS/FAIL escritos em `artifacts/reports/e2e-report.md`; nada é declarado concluído sem execução.

## 14. Documentação exigida

`README.md` passo a passo (pré-requisitos, instalação Windows/Linux, primeira subida, URL/dashboard, Jupyter, MLflow, treinamento, promoção, consultas SQL, inferência, logs, testes, troubleshooting); `docs/installation/WINDOWS.md`, `LINUX.md`; `docs/operations/{START_STOP,LOGS,JUPYTER,MLFLOW,POSTGRES,RUSTFS,BACKUP_RESTORE}.md`; `docs/commands/COMMANDS.md` (cada comando com finalidade, parâmetros, saída esperada, erros e reparos); `docs/architecture/{ARCHITECTURE,DATA_FLOW}.md`; ADRs (RustFS, schemas, coleta de logs, separação Workbench local/produção, namespace e PVC, segurança).

## 15. Sequência de implementação pelo Codex

1. Gerar arquivos repo e este SPEC como contrato, sem excluir campos silenciosamente.
2. Setup e preflight; validação de contexto seguro.
3. Dockerfiles, Helm/manifests, Secrets e storage.
4. PostgreSQL / migrations / catálogo.
5. RustFS, RabbitMQ, MLflow.
6. Jupyter pronto e notebook 00.
7. Dados sintéticos, feature engineering e 30 treinamentos.
8. Registry, promoção, FastAPI/Celery e persistência.
9. Collector, dashboard e logs.
10. Runbooks, comandos e e2e.
11. Reconciliar qualquer alteração nas migrations com a seção DDL e catálogo deste documento.

**Restrições de honestidade operacional:** não inventar resultados de testes, não presumir Rancher instalado, não afirmar que a infra Azure real foi testada, não realizar ações destrutivas, e não marcar componente como pronto se a integração estiver quebrada.

## Adendo de runtime — 26/10/2026

Por autorização do usuário, Docker Compose substitui Kubernetes no desenvolvimento
local. Kubernetes/Helm permanecem para staging/produção. A exigência anterior de
runtime local exclusivamente em pods fica substituída por esta decisão (ADR 007).
Preservar dados e notebooks; remover recursos Kubernetes da POC após validação da
migração. Pipeline verifica dependências de cada container. RustFS permanece.

## Adendo C3 — 28/10/2026

Treinamento no Jupyter via SDK/HTTP; metadados exclusivamente PostgreSQL (bancos
planejamento_db e mlflow_db); binários ajustados no RustFS. Serviço ingestion recebe
e valida a base agregada. Modelo serializado inclui lógica de previsão; inferência
não executa fit. Aprovação auditada fixa run/código/hashes; publicação explícita cria
um container/API por modelo. Notebook 09 e ADR 008 definem o fluxo local atual.
Referências Kubernetes anteriores não equivalem a GKE/GCS/Artifact Registry implantados.
