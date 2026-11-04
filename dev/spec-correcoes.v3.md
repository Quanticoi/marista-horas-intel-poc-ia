# SPEC — Correções V3 | POC IA Horas Inteligentes
**Versão:** 3.0  
**Data:** 04/11/2026  
**Destino:** Codex — repositório `Quanticoi/marista-horas-intel-poc-ia`, branch `development`  
**Classificação:** especificação corretiva, não autorização para apagar dados, promover modelos ou alterar a arquitetura institucional.

> **Missão:** transformar a POC tecnicamente funcional em uma **bancada de validação manual, observável e auditável do C3**, na qual um cientista consiga identificar sem ambiguidade o que treinou, qual experimento/run e versão do modelo foram produzidos, onde está o binário no RustFS, quais registros existem em PostgreSQL, qual versão foi carregada na inferência e qual proposta de Planilha Turmas foi entregue via API. IDs e hashes permanecem como identidade técnica e prova de integridade; **nomes e contexto acadêmico legíveis são a interface humana**.

## 0. Contexto obrigatório, fontes e limites

### 0.1 Estado confirmado antes desta SPEC
- `README.md` possui o diagrama Mermaid **“Inicialização da plataforma e serving independente do Jupyter”**, inserido diretamente na `development` no commit `b02739caf75c`. Preservar o diagrama e sua explicação; refinar apenas para manter correspondência com a implementação.
- POC atual usa **Docker Compose**. O Jupyter é a bancada do cientista, análoga ao futuro Workbench. MLflow 3.11.1 com Tracking/Registry e backend PostgreSQL; RustFS como storage S3; PostgreSQL do negócio; FastAPI, inferência, monitoramento, RabbitMQ e Celery.
- A SPEC V2 implementou geração por API/worker, campanhas persistentes, governança, lineage N:N e notebooks `00` a `09`. Testes publicados da V2 indicam 16/16 critérios PASS, 79 testes e treinamento de 500 **identidades DEMO**. Não equiparar esses 500 treinos a 500 séries acadêmicas diferentes; o relatório consultado mostra apenas um SHA-256 distinto de `model.pkl` entre os 500 ensaios.
- O serving DEMO usa carregamento sob demanda e cache LRU de até quatro versões por processo; **startup do serviço != todos os modelos já residentes na memória**. O fluxo legado de API dedicada depende de publicação explícita.
- `HI-LINEAGE/1.0` existe em `src/common/lineage.py`, `planning.lineage_entities`, `lineage_edges`, `proposal_model_usage` e manifests `lineage/poc/planilha-turmas/`. Ele é ponto de partida; **não inventar uma segunda taxonomia incompatível**.
- `poc-planilha-turmas-v1` é contrato **provisório**, com campos acadêmicos desconhecidos nulos e regras V4.4 não demonstradas `NOT_EVALUATED`. Não afirmar que foi homologado.
- A referência arquitetural é C2/C3 V3 e Diagrama de Sequência V3. A referência de negócio é `REQ_InteligenciaeOtimizacaodeHorariosAcademicos_V4.4`. O objetivo imediato desta V3 é **operacionalização, nomenclatura, rastreabilidade e aceite manual do C3**, não implementar a totalidade das regras de negócio.

### 0.2 Arquivos que o Codex deve inspecionar ANTES de editar
`README.md`; `dev/spec-correcoes.md`; `dev/spec_correcoes.v2.md`; `docs/architecture/{ARCHITECTURE,LINEAGE,FUNCTIONAL_COVERAGE}.md`; `docs/operations/{OPERATIONS_V2,MLFLOW_MODEL_ORGANIZATION,INFERENCE_NOTEBOOK,RESET_POC}.md`; `compose.yaml`; `deployment/scripts/{compose.ps1,journey.sh,generate_compose.py}`; `src/common/lineage.py`; `src/operations/{jobs,training,generation,governance}.py`; `src/inference/{journey,runtime,model_api}.py`; `src/api/{operations,proposal_contract,lineage}.py`; `src/persistence/{journey,lineage}.py`; `sql/ddl/*`; `notebooks/*.ipynb`; `tests/**`; relatórios de aceite V2.

Registrar antes da mudança em `artifacts/reports/v3/inventory-before.json`: HEAD, contagem de runs/modelos/propostas, volumes, status dos 11 serviços, versões dependências, rotas de API, lista de notebooks, saúde de MLflow, bucket/prefixos, estado de migrations. **Não imprimir credenciais.**

### 0.3 Regras de segurança e preservação
1. **NÃO** executar reset destrutivo na stack principal, `docker compose down -v`, limpeza do bucket, exclusão de runs/experimentos, alteração destrutiva de schemas ou promoção automática.
2. Preservar modelos, artefatos, snapshots, runs, propostas, aliases e notebooks editáveis. Criar migrações **aditivas**, backfill não destrutivo e marcadores explícitos para legado incompleto.
3. Não escrever diretamente nas tabelas internas `mlflow_db`; utilizar SDK/REST oficiais. Nunca alterar manualmente nomes de pastas/objetos sob `mlflow/`: esse prefixo é controlado pelo MLflow.
4. Todos os exemplos de credenciais devem referenciar `.env` e Secret/variável de ambiente, sem exibir valores. Não registrar payloads acadêmicos sensíveis em tracing.
5. Testes destrutivos apenas em Compose project **isolado, descartável e com ownership validado**.
6. PR/commit apenas quando explicitamente solicitado; nesta SPEC o Codex poderá implementar e reportar, mas deve descrever claramente os diffs e evidências antes de considerar concluído.
7. Manter a separação: **notebook treina/submete/inspeciona; serviço API, worker, MLflow, inferência e monitoramento permanecem de pé independentemente do kernel**.

## 1. Resultado esperado — o “teste de mesa” do cientista

A pessoa deve conseguir executar a sequência abaixo **sem investigar hashes aleatórios**:

1. `compose.ps1 start`; abrir dashboard, Jupyter, MLflow e RustFS; confirmar plataforma saudável.
2. Escolher cenário acadêmico DEMO com rótulo legível: ciclo, campus, curso, período, snapshot e família de modelo.
3. Executar notebook `04` para modelo individual ou `05` para campanha pequena (3–5 modelos), a partir de entradas explícitas.
4. Ver em uma tabela da saída: **nome de experimento**, **run_name**, `run_id` (curto + completo), `model_key` e nome amigável, versão, status, dataset/snapshot, algoritmos, métricas, duração e links que abrem exatamente esses registros no MLflow.
5. Abrir MLflow: localizar experimento/run pelo nome, conferir tags, métricas, artefato e versão no Registry. A **run** e a **versão** devem se relacionar por IDs nativos sem ambiguidade.
6. Abrir RustFS: localizar um **índice/manifest legível da mesma execução** e usar sua referência `artifact_uri` para encontrar os arquivos reais do modelo em `mlflow/`. Conferir `model.pkl`, `MLmodel`, `requirements.txt` e SHA-256. Não duplicar binário só para formar pastas legíveis.
7. Abrir PostgreSQL: consultar catálogo de auditoria legível por `model_key`, `run_id`, `model_version` ou `proposal_id` e navegar para as demais entidades. Confirmar separação `mlflow_db` vs `planejamento_db`.
8. Sem reabrir o treino, usar notebook `02` como cliente HTTP para solicitar geração DEMO por API/worker com a versão explícita; acompanhar status até `COMPLETED`, consultar JSON versionado, validar linhas e persistência.
9. Reiniciar somente inferência; repetir a leitura/predição pela API usando versão registrada; confirmar que o binário é restaurado sem Jupyter e que a telemetria identifica o modelo.
10. Ver no notebook `08` ou na visão de auditoria a árvore **Proposta → inferências → modelos/versões → runs → experimento → dataset/snapshot → RustFS**, com links e resultados `VERIFIED | LEGACY_PARTIAL | MISSING | MISMATCH`.
11. Exportar **um pacote de evidências** (JSON + Markdown + CSV de inventário, sem credenciais) com resultados automáticos e campos de conferência manual `PASS/FAIL/NOT_CHECKED`.
12. Realizar um teste negativo: versão inexistente, artefato corrompido em stack isolada ou tag conflitante deve falhar **sem servir modelo errado**, sem perder dados e com mensagem diagnóstica segura.

Critério global: **um avaliador independente consegue identificar tudo a partir de uma única chave funcional**, sem manipular manualmente JSON cru, procurar pelo hash nas 500 versões ou abrir ferramentas de desenvolvimento.

## 2. Taxonomia de nomes legíveis (não substituir IDs nativos)

### 2.1 Hierarquia conceitual
`solution → environment → domain → academic_cycle → dataset/snapshot → model_family → model_key → training_campaign → experiment/run → registered_model/version → inference → proposal`.

**Identidade estável** (`model_key`) e **identificadores técnicos nativos** (`run_id`, UUIDs, versão, SHA-256) devem coexistir com `display_name`, `business_label`, `experiment_name`, `run_name` e descrição pesquisável.

| Campo | Finalidade | Exemplo ilustrativo |
|---|---|---|
| `solution_id` | Solução | `horarios-inteligentes` |
| `environment` | Ambiente real da execução | `poc` |
| `domain` | Domínio | `planilha-turmas` |
| `cycle_code` | Ciclo legível | `2026-2` |
| `campus_code` | Campus do escopo, quando disponível | `CTA` |
| `course_code` | Curso | `ENG-SOFT` |
| `period_code` | Período/turno | `P03-N` |
| `model_family` | Família preditiva | `demanda-alunos` |
| `model_key` | Chave estável e única | `hi.pt.demanda.CTA.ENG-SOFT.P03-N` |
| `model_display_name` | Nome para UI | `Planilha Turmas • CTA • Engenharia de Software • 3º período • Noturno` |
| `experiment_name` | Agrupador legível, **não por versão** | `HI/POC/PlanilhaTurmas/Demanda/2026-2` |
| `run_name` | Tentativa identificável | `CTA-ENG-SOFT-P03-N__ridge__20261104T170000Z__a01` |
| `training_campaign_id` | ID persistente da campanha | UUID |
| `campaign_display_name` | Nome de campanha | `POC-2026-2-ValidacaoManual-03Modelos` |
| `registered_model_name` | Registry nome estável | Igual `model_key` quando elegível |
| `model_version` | Versão nativa MLflow | `3` |
| `artifact_sha256` | Integridade, não identificação humana | 64 caracteres hex |
| `proposal_id` | Proposta única da API | UUID |
| `proposal_display_name` | Rótulo legível | `Planilha Turmas 2026-2 • Proposta IA • DRAFT` |

**ATENÇÃO:** exemplos de códigos acima **não são fatos do cadastro acadêmico**. Para dados DEMO, mapear códigos sintéticos verdadeiros para labels DEMO explícitos; nunca apresentar nome real de campus/curso inventado como se viesse do PRIME. Dados sem identificação devem ser rotulados `DEMO-C1`, `DEMO-CR1`, etc., não preenchidos por suposição.

### 2.2 Normas de naming
- `model_key`: imutável para a mesma série/escopo; NÃO colocar hash de run, data, versão ou nome de operador na chave. O nome deve ser determinístico de uma **identidade funcional real**, com validação de colisões.
- `run_name`: humano, pode incluir data UTC, algoritmo, tentativa e sufixo curto, mas manter `run_id` real sempre.
- `experiment_name`: por domínio/ciclo ou família/campanha conforme dicionário fixo. **Não criar automaticamente 500 experimentos** nem um experimento para cada versão.
- `campaign_display_name`: permitir filtro e navegação de conjunto de modelos.
- Limitar comprimento e caracteres conforme SDK MLflow e SQL; normalização Unicode e colisões documentadas. Não usar nomes acadêmicos pessoais ou PII.
- Registrar `display_name`/códigos de domínio como **metadados de apresentação**, não sobrescrever PKs. Se um curso mudar de nome, preservar `course_id`, código, histórico do nome e snapshot.
- Nomes legados `planilha-turmas-demo`, `C1-CR1-P1` e `hi.demo.*` devem continuar válidos. Backfill apenas com mapeamento confiável; sem ele, `LEGACY_PARTIAL`.

## 3. Taxonomia de tags única: `HI-LINEAGE/1.1` (extensão compatível)

Não substituir `HI-LINEAGE/1.0`; definir **extensão aditiva documentada** `HI-LINEAGE/1.1` e mapeador retrocompatível.

### 3.1 Tags obrigatórias nos objetos onde aplicáveis
Grupos obrigatórios, com nomes em `snake_case`:

**Contexto:** `solution_id`, `environment`, `domain`, `source_type`, `cycle_code`, `academic_cycle_id`, `campus_code`, `course_code`, `period_code`, `model_family`.

**Dados:** `snapshot_id`, `snapshot_sha256`, `dataset_sha256`, `dataset_schema_version`, `data_as_of_utc`, `query_version`.

**Treino:** `training_campaign_id`, `campaign_display_name`, `operation_job_id`, `training_execution_id`, `experiment_id`, `experiment_name`, `run_id`, `run_name`, `algorithm`, `code_version`, `config_hash`, `feature_schema_hash`.

**Modelo:** `model_key`, `model_display_name`, `registered_model_name`, `model_version`, `artifact_uri`, `artifact_sha256`, `model_signature_hash`, `validation_status`.

**Inferência e proposta:** `inference_id`, `proposal_id`, `proposal_revision`, `proposal_schema_version`, `ruleset_version`, `ruleset_hash`, `correlation_id`, `trace_id` quando disponível.

Nem todos os campos cabem como tag em todo objeto: tags devem ser **índices de busca concisos**; campos extensos e relacionamentos N:N ficam em PostgreSQL e manifest JSON. Nunca inventar `run_id` para snapshot não treinado ou `proposal_id` para treino isolado. A ausência legítima deve ser `null`/não aplicável, não um ID falso.

### 3.2 Contrato de tipo e semântica
- IDs: UUID ou identificador nativo preservado, sem reciclar `execution_id` para significar simultaneamente várias operações.
- `model_version`: inteiro positivo, versão Registry. `proposal_revision`: revisão do negócio, independente.
- Hashes: SHA-256 de bytes reais, com distinção entre `snapshot_sha256`, `dataset_sha256`, `artifact_sha256` e `manifest_sha256`.
- Timestamps UTC ISO 8601, com timezone.
- Status são enums bem definidos; tag `validation_status` **não** significa autorização técnica nem acadêmica.
- Identidade de versão aprovada não fica somente em alias mutável; consultar estado auditável PostgreSQL e validar concordância com Registry.
- Dicionário canônico versionado: `docs/contracts/HI_TAGGING_STANDARD.md` com tabela nome, tipo, significado, origem, destino, obrigatoriedade, cardinalidade, exemplo e compatibilidade.

## 4. Onde tudo deve aparecer

### 4.1 Jupyter / Workbench
Cada notebook de treinamento (`01`, `04`, `05`) deve exibir no início **contexto da execução**, tabela dos parâmetros, dataset/snapshot e uma seção final **“Onde conferir”**:

| Destino | Elemento apresentado |
|---|---|
| MLflow | Nome do experimento; link para run, Registry/modelo/versão |
| RustFS | Bucket, chave do manifest e prefixo exato do artefato (com botão de copiar como texto, se aplicável) |
| PostgreSQL | Banco/schema/tabela e SQL parametrizada segura |
| API | Endpoint, método, status, `job_id`, `proposal_id`, link Swagger |
| Dashboard | URL, `correlation_id`, status, traces |
| Resultado | IDs completo/curto, versão, nome legível e checks de integridade |

**Nunca exibir apenas hash/UUID.** Exibir nome + resumo + identificador completo copiável e indicar quando o nome é DEMO.

Notebook `06`: comparação por mesmo snapshot/janela/target, com ranking de métricas e links. Notebook `07`: mostrar candidatas, status de aprovação, aliases e efeito da revogação. Notebook `08`: hub de auditoria e reconciliador N:N. Notebook `09`: manter pré-visualização não destrutiva; controlador externo preservado.

### 4.2 MLflow UI
- Nomear experimentos e runs como especificado.
- Adicionar tags de contexto às runs e **Model Versions** nas APIs de registro; metadados longos ficam nos artifacts/manifests.
- Para cada versão, registrar descrição curta que inclua `model_display_name`, ciclo, snapshot, algoritmo, `run_id` curto, data UTC, status DEMO e referência de catálogo.
- Quando uma nova versão for registrada, verificar `run_id`, source, `artifact_sha256`, status FINISHED e esquema de entrada/saída.
- Tags de run e Model Version devem ser coerentes nos campos compartilhados. Falhar com erro explícito quando divergirem, sem promover.
- Não exigir que a UI MLflow exponha “pastas legíveis” sob o diretório interno `mlflow/`; utilizar manifest/índice e links nativos.

### 4.3 RustFS
**Não renomear nem mover** `mlflow/<experiment>/models/<hash>/...` porque é gerenciado pelo MLflow. Adicionar **índices/manifestos de catálogo legíveis** sob prefixo independente, por exemplo:

```text
pucpr-poc/
  mlflow/...                                # artefatos gerenciados pelo MLflow; intactos
  snapshots/<snapshot_id>/manifest.json    # snapshot canônico; intacto
  lineage/poc/planilha-turmas/
    catalog/
      cycles/2026-2/
        models/<model_key>/
          versions/v0003/manifest.json     # referência, SEM copiar o binário
    campaigns/<campaign_id>/manifest.json
    inferences/<inference_id>/manifest.json
    proposals/<proposal_id>/revisions/1/manifest.json
```

Manifest de versão deve conter: `manifest_schema_version`, `environment`, `source_type`, `cycle_code`, `model_key`, `model_display_name`, `experiment_name`, `experiment_id`, `run_name`, `run_id`, `registered_model_name`, `model_version`, `artifact_uri`, **S3 object keys reais**, nome/tamanho/hash dos arquivos, `snapshot_id`, `dataset_sha256`, `code_version`, `algorithm`, `created_at_utc`, `status_at_creation` e referência cruzada à tabela SQL. Metadados mutáveis como `current_approval_status` devem ser consultados da autoridade relacional e não sobrescrever manifests imutáveis.

- Usar escrita condicional com idempotência, conferência byte a byte; jamais sobrescrever em colisão.
- Distinguir `artifact_uri` (`models:/`, `mlflow-artifacts:/`, `s3://`) da **chave física** da API S3. Resolver com cliente MLflow + SDK S3; não fazer concatenação presumida de caminhos.
- Para S3, metadata object/header tem limitações de tamanho e semântica; manifest JSON é fonte de contexto; tags S3 adicionais apenas se suportadas pelo RustFS da POC e verificadas em teste.
- Manifest não deve conter tokens, strings de conexão, nomes pessoais de estudantes, payload integral, segredos ou dados institucionais sensíveis.
- Criar **índice legível por ciclo/campanha/modelo**, consultável via notebook 08 e API. Não copiar centenas de binários para gerar organização estética.

### 4.4 PostgreSQL
`mlflow_db` é exclusivamente administrado pelo MLflow. No `planejamento_db.planning`, acrescentar **views/materializações ou tabelas de catálogo aditivas** quando necessário:
- `planning.v_model_inventory`: `model_key`, display name, contexto, última versão, último run, snapshot, status técnico, campanha, hashes e links;
- `planning.v_training_inventory`: campanha, job, tentativa, modelo, experimento, run, métricas, duração, status, erros sanitizados;
- `planning.v_proposal_lineage_readable`: proposta e cada linha → inferências, run, versão, snapshot, manifestação de integridade;
- `planning.v_storage_manifest_inventory`: modelo/versão → `manifest_uri`, `artifact_uri`, `artifact_sha256` (links/refs, não duplicar dados de artefato sem consistência).

Usar SQL de leitura parametrizado, limites e índices para 500+ modelos. Não tentar FK entre databases. Evitar view que produz combinatória incorreta ao fazer JOIN N:N: uma proposta com 3 modelos deve indicar 3 contribuições com linhas vinculadas, não duplicar oferta final. Implementar consultas por `proposal_id`, `model_key`, `run_id`, `snapshot_id` e `campaign_id`. Para divergências, retornar `MISMATCH`, não mascarar faltas com strings genéricas.

Criar `sql/queries/manual_validation_v3.sql` (ou arquivos menores) com consultas **read-only**, comentários e parâmetros sem credenciais, além de `docs/operations/SQL_VALIDATION_V3.md` com resultados esperados.

### 4.5 API, dashboard e monitoramento
Reutilizar rotas V2; acrescentar **visão composta de auditoria** somente se o retorno atual não for suficiente:
- `GET /v1/lineage/graph?...` continua sendo fonte para grafo;
- `GET /v1/governance/models?...` continua listando Registry;
- Propor `GET /v1/audit/model?model_key=...&version=...` e `GET /v1/audit/proposal/{proposal_id}` como **agregadores de metadados**, se necessário; proteger com Bearer e limites.
- Expor separadamente estados: serviço `healthy`, Registry acessível, versão registrada, modelo aprovado, modelo em cache, artefato verificável. `healthy` nunca equivale a 500 modelos carregados.
- Reutilizar endpoint existente `/internal/draft/cache`; se adicionar endpoint operacional, validar autenticação e não vazar caminhos internos sensíveis.
- Dashboard deve permitir filtrar `model_key`, `run_id`, `campaign_id`, `proposal_id`, `correlation_id` e abrir links correspondentes; não substituir log por apenas um contador.
- Diferenciar `NOT_FOUND` (identidade não existe), `MISSING` (referência não encontrada), `MISMATCH` (divergência detectada), `LEGACY_PARTIAL` (dado histórico incompleto) e `VERIFIED` (verificação completa).

## 5. Bootstrap da plataforma e independência de serving

O README já possui o diagrama de startup; validar o código contra ele:

1. Um único comando sobe o conjunto de serviços `api`, `inference`, `mlflow`, `monitoramento`, `worker`, `postgres`, `rustfs`, `rabbitmq`, `dashboard`, `jupyter` e demais componentes previstos.
2. MLflow sobe com backend `mlflow_db`, artefatos em RustFS, Tracking/Registry acessíveis e sem SQLite fallback.
3. Inferência sobe **mesmo sem modelos**. Falta de modelo deve retornar erro de negócio claro, não tornar todo serviço unhealthy.
4. O modelo **não precisa ser treinado nem registrado durante o startup**. Após treinamento, Registry e storage estão disponíveis imediatamente.
5. No caminho de inferência autorizado, resolver versão explícita (ou alias aprovado), validar run/hash/esquema, carregar o modelo do RustFS e registrar `inference_id`.
6. Reiniciar **somente** inferência: API/MLflow/monitoramento/worker continuam; modelos são recuperados em novas chamadas, sem abrir Jupyter.
7. Revogação bloqueia chamadas do modo `APPROVED`, inclusive se modelo já estava em cache; **não presumir que invalidação de cache substitua validação de autorização**.
8. Para POC, cache LRU 4 por processo continua aceitável; documentar impactos na memória, cold/warm hits, misses, eviction e métricas. Pré-carregamento é **opcional e não requerido**; proibir carregar 500 modelos automaticamente por exigência artificial.
9. Provar operação com duas versões e três modelos distintos, e não apenas o modelo legado `planilha-turmas-demo`.
10. Reconciliar o papel da API/worker: Jupyter faz treino e solicita geração; **worker compõe e persiste DRAFT** na jornada V2. Jornada 01 legada deve continuar marcada como demonstração, não padrão de persistência operacional.

## 6. Plano de testes manuais — `MANUAL_ACCEPTANCE_V3.md`

Criar `docs/operations/MANUAL_ACCEPTANCE_V3.md` como **roteiro passo a passo para ser executado por uma pessoa**. Cada etapa deve trazer:
- pré-condições, comando/célula exatos, URL/serviço, parâmetro a preencher, evidência esperada, consulta de conferência e resultado `PASS/FAIL/NOT_CHECKED`;
- tempo de observação pode ser registrado, mas não prometer SLA;
- não depender de dados/IDs efêmeros hardcoded de ensaios antigos;
- usar nomes legíveis e exemplos **explicitamente DEMO**;
- informar em que tela e seção do MLflow localizar runs, métricas e versões; no RustFS, bucket/prefixo do manifest e artefato gerenciado; no PostgreSQL, SQL exato e tabela;
- instruções para checar modelo com run distinto, nova versão, troca de versão, inferência após restart e proposta;
- incluir links do relatório para navegação sem copiar credenciais.

### 6.1 Caso de teste M01 — plataforma fria sem modelos
Usar stack **isolada** limpa; `compose up`; confirmar readiness. Ver API, MLflow, monitoramento e inferência saudáveis sem notebook; consultar inventário vazio; não criar modelo automaticamente.

### 6.2 M02 — treino 3 modelos distintos
Usar dataset(s) DEMO **com séries ou parâmetros intencionalmente diferentes** (documentar qual variação); treinar individualmente ou em campanha. Mostrar experimento e run por nome, métricas, versões e artefatos. Comparar `model.pkl` e explicar por que hashes iguais podem ser válidos caso os bytes sejam iguais; não chamar “500 modelos diferentes” a 500 execuções de mesmo pipeline/dados.

### 6.3 M03 — navegação MLflow
Localizar experimento pela convenção; filtrar runs por `model_key` e campanha, abrir runs, confirmar parâmetros/métricas/tags; abrir Registry por nome, confirmar versões, run e source. Registrar links HTTP *funcionais no ambiente real*.

### 6.4 M04 — RustFS
Encontrar manifest por prefixo legível. Abrir referência ao binário sob `mlflow/`. Validar 3 arquivos e hashes contra MLflow; salvar lista de objetos `Key | Bytes | SHA256 | Run | Model | Version`. Sem alterar objeto.

### 6.5 M05 — PostgreSQL
Executar SQL read-only de catálogo, tabela de runs/jogs, grafo, propostas. Confirmar `model_key` igual entre sistemas, `run_id`, versão, snapshot, `artifact_sha256` e propostas; comparar quantidade de ofertas da API com banco.

### 6.6 M06 — inferência e proposta via API
Notebook 02 em modo `GENERATE_AND_VALIDATE`, `execute_write=True` e confirmação explícita: obter `job_id`, esperar status persistente, checar `inference_id`, proposta DRAFT, payload JSON paginado, SQL e manifest. Reexecutar com mesma chave: idempotência; chave nova gera nova proposta, sem sobrescrever original.

### 6.7 M07 — reinício dos serviços
Treinar e registrar versão. **Parar Jupyter** ou reiniciar kernel; reiniciar **somente inferência**; chamar a API e verificar que modelo é recuperado pelo Registry/RustFS. Capturar cache before/after e logs. O cenário de aprovação/revogação deve ser testado só com modelo DEMO e aprovação explícita.

### 6.8 M08 — 30/500 escala com distinção clara
Rodar campanha 30 para validação operacional; 500 pode reutilizar evidências V2 **somente se compatíveis com o código atual**, sem repetir custo de execução desnecessariamente. Se repetir, usar stack isolada e medir CPU/RAM/storage, duração, falhas, taxa de sucesso. Testar pelo menos 3 identidades com modelos realmente diferentes no cenário M02; não prometer 500 residentes.

### 6.9 M09 — falhas controladas
Ambiente descartável: MLflow indisponível, objeto ausente/alterado, versão inexistente, status revogado, API sem token, snapshot incompatível. Esperado: não servir versão errada; erros seguros e rastreáveis; sem dados corrompidos.

### 6.10 M10 — reset
Notebook 09 apenas `preview` e relatório; teste destrutivo pelo controlador externo em projeto isolado, rebootstrap `empty` e `demo-ready`, comprovando ausência de runs, Registry, objetos e propostas anteriores. Não executar factory reset na stack principal.

### 6.11 M11 — auditoria reversa
Começar somente com `proposal_id`; localizar modelos/versões, runs, experimento e RustFS. Repetir partindo de `model_key` e `run_id`. Validar contagem N:N, integridade e `VERIFIED`. Caso legado deve aparecer `LEGACY_PARTIAL`, não `VERIFIED` falso.

### 6.12 M12 — checklist final
Um relatório curto por sessão, contendo `manual_session_id`, data UTC, commit, ambiente, nomes legíveis, IDs completos, links locais, evidências, checks manuais e limitações. Nunca declarar `PASS manual` se ninguém realmente conferiu a UI; marcar `NOT_CHECKED` e deixar pronto para preenchimento.

## 7. Implementação sugerida — módulos e arquivos

**Reutilizar antes de criar.** Proposta de estrutura aditiva (ajustar aos módulos existentes, não duplicar responsabilidades):

```text
src/common/tagging.py                # taxonomia, normalização, validação, compatibilidade
src/workbench/manual_validation.py   # relatório navegável e reconciliação para notebooks
src/workbench/catalog_views.py       # tabelas legíveis e links
src/persistence/catalog.py           # consultas read-only e views/indices
src/api/audit.py                     # agregação segura, somente se rotas atuais insuficientes
sql/ddl/008_tagging_catalog.sql      # somente se schema exigir alteração aditiva
sql/queries/manual_validation_v3.sql
docs/contracts/HI_TAGGING_STANDARD.md
docs/operations/MANUAL_ACCEPTANCE_V3.md
docs/operations/SQL_VALIDATION_V3.md
artifacts/reports/v3/              # evidências reais, com referências
tests/unit/test_tagging_v3.py
tests/integration/test_catalog_v3.py
tests/e2e/test_manual_journey_v3.py
```

Nenhum módulo novo é obrigatório se o existente comportar a implementação sem acoplamento. Codex deve documentar **antes/depois** e justificar adições. Não criar duplicatas `dev/` vs `deployment/scripts/`.

## 8. Critérios de aceite V3 — não negociáveis

| ID | Evidência/condição para PASS |
|---|---|
| V3-01 | `README.md` preserva diagrama de startup C3; serviços sobem independentes do notebook |
| V3-02 | MLflow UI mostra nome de experimento/run legível, tags consistentes e Registry por modelo estável |
| V3-03 | Notebook 04 gera treino real, run, versão e “Onde conferir” com links verificáveis |
| V3-04 | Notebook 05 gera campanha real com nome, contagens, progresso, runs, versões e filtros |
| V3-05 | RustFS contém manifest legível que referencia **sem cópia** binário real gerenciado pelo MLflow |
| V3-06 | Correspondência byte a byte `model.pkl` e hashes entre MLflow, RustFS e catálogo |
| V3-07 | PostgreSQL apresenta inventário legível e consulta inversa sem duplicação indevida N:N |
| V3-08 | `proposal_id` permite localizar `inference_id → version → run → experiment → snapshot → storage` |
| V3-09 | Notebook 02 inicia geração por API/worker e valida proposta persistida, sem treino acidental |
| V3-10 | Modelo registrado é carregado por inferência após restart **sem Jupyter** |
| V3-11 | Serviço saudável sem modelos; estado de modelo disponível/carregado/aprovado é distinto |
| V3-12 | Aprovação/revogação técnica não é confundida com decisão acadêmica; fail-closed |
| V3-13 | Tabelas, tags e manifests preservam runs/modelos antigos e classificam legado parcial |
| V3-14 | Pelo menos 3 experimentos/modelos DEMO com diferenças deliberadas e documentadas |
| V3-15 | Sessão manual orientada por roteiro consegue identificar todos os artefatos em cada UI |
| V3-16 | Testes negativos não geram resultados silenciosamente inválidos |
| V3-17 | CI em checkout limpo executa testes automatizados, sem depender de IDs de relatórios históricos |
| V3-18 | Relatório final distingue **AUTO_PASS**, **MANUAL_PASS**, **MANUAL_NOT_CHECKED** e **BLOCKED** |
| V3-19 | Reset em stack isolada preserva arquivos protegidos; reset da stack principal não é executado |
| V3-20 | Nenhuma perda de runs, volumes, artefatos, notebooks editáveis, aprovações ou propostas históricas |

**Regra:** teste com mock não prova interação real com MLflow/RustFS/PostgreSQL. Teste HTTP de `/health` não prova que a versão foi carregada. Hash idêntico entre 500 artefatos não prova 500 comportamentos independentes. “Manual” nunca recebe PASS se a UI não foi realmente observada.

## 9. Ordem de execução mandatória para o Codex

1. **Diagnóstico e backup de evidência:** inventário do HEAD, runtime, estados de serviços e fontes; comparação V2, sem alterações.
2. **Dicionário de taxonomia:** design `HI-LINEAGE/1.1`, sem regressão do 1.0, aliases legados, normalização e testes.
3. **Implementação MLflow:** nomes legíveis, tags, descrição e verificações no registro, sem reescrever versões antigas.
4. **Índice RustFS:** manifest legível e links físicos reais; idempotência e conferência de hash.
5. **Catálogo PostgreSQL:** views SQL e queries parametrizadas, sem escrever no banco MLflow manualmente.
6. **Notebooks 04/05/06/07/08:** exibir contexto humano, links e execução governada; 01 e 02 continuam válidos.
7. **Inferência e startup:** testes de recuperação sem notebook, cache/readiness/seleção de versão/authorização.
8. **README e roteiro manual:** atualizar arquitetura, seção “Onde conferir”, SQL e checklist, sem prometer features não implementadas.
9. **Teste automatizado isolado + CI:** integração real, falhas controladas, preservação de dados; não usar reset principal.
10. **Sessão manual:** fornecer roteiro e pacote de evidências; executar verificações de UI **somente se existir ferramenta de navegador real disponível**. Caso contrário, resultado `MANUAL_NOT_CHECKED` para conferência humana.
11. **Relatório de entrega:** arquivo `artifacts/reports/v3/acceptance-v3.md` contendo matriz V3-01...V3-20, status fundamentado, commit testado, limitações, gaps e comandos reproduzíveis. Nunca escrever `20/20 PASS` sem evidência.

## 10. Formato do relatório de execução

Para cada teste: `test_id`, `status`, `evidence_file`, `git_commit`, `environment`, `executed_at_utc`, `source_type`, `experiment_name`, `run_name`, `run_id`, `model_key`, `model_version`, `artifact_uri`, `artifact_sha256`, `proposal_id` quando aplicável, `checks`, `limitations`, `manual_observation`.

Criar índice HTML **estático e local** opcional, ou Markdown com tabelas e links, respeitando política de exposição de endpoints. Nenhuma API externa, Grafana ou serviço novo é necessário somente para exibir o catálogo. O dashboard HTML existente pode receber uma página de rastreabilidade se isso simplificar a conferência.

## 11. Definição de conclusão

**A V3 só estará efetivamente concluída quando um operador puder abrir a POC e, usando nomes legíveis, seguir o mesmo modelo da criação no Jupyter até o MLflow, versão no Registry, binário no RustFS, registros PostgreSQL, inferência em serviço independente e proposta retornada pela API — sem depender de adivinhação de hashes/UUIDs.**

O desenho C3 é validado **tecnicamente como POC**, com dados DEMO e contrato provisório. Qualquer afirmação sobre homologação V4.4, GKE/Cloud SQL/GCS, disponibilidade corporativa, SLO ou modelos acadêmicos reais deve permanecer identificada como **não demonstrada** até existir evidência própria.
