# SPEC — Correções e evolução da POC IA | Horas Inteligentes

**Versão:** 1.1  
**Data:** 2026-11-04  
**Destino:** Codex — implementação controlada no repositório `Quanticoi/marista-horas-intel-poc-ia`, branch `development`  
**Natureza:** especificação de implementação, contratos, migrações, documentação e testes de aceite.  
**Escopo:** validação técnica da arquitetura de solução para Planilha Turmas; não é homologação das regras acadêmicas finais nem implantação GCP.

> **Ordem central ao Codex:** leia o repositório e todas as referências listadas antes de editar. Faça inventário do que existe, reutilize código e tabelas, crie migrações aditivas e preserve dados/runs/volumes/modelos/notebooks/credenciais. Não simplifique nem remova o fluxo demonstrado. Não faça `docker compose down -v`, reset de storage, exclusão de experimentos ou promoção de modelos durante a implementação ou testes rotineiros. **Exceção específica:** implementar a ferramenta de reset descrita na seção 4.6, mas executá-la apenas mediante solicitação humana, escopo validado e confirmação forte; sua implementação não é autorização para rodar o reset nesta tarefa. Execute o máximo possível de testes reais e registre provas verificáveis, distinguindo PASS de NÃO EXECUTADO. Não declare sucesso baseado apenas em testes unitários ou mocks.

## 0. Fontes de verdade, contexto e precedência

1. **Implementação atual:** branch `development` do repositório GitHub. Arquivos a inspecionar: `README.md`, `spec.md`, `compose.yaml`, `dev/generate_compose.py`, `notebooks/01_jornada_completa_planilha_turmas.ipynb`, `src/workbench/*`, `src/mlops/*`, `src/data/*`, `src/training/*`, `src/inference/*`, `src/persistence/*`, `src/api/*`, `sql/ddl/*`, `tests/*`, `docs/operations/*`, `artifacts/reports/*`.
2. **Arquitetura-alvo:** `PUCPR - Otimização de Horários Inteligentes - Arquitetura de Componentes - V3`, `Arquitetura de Containers - V3` e `Diagrama de Sequência - V3`. Segregação: Workbench/Jupyter → MLflow/Tracking/Registry → artefatos Object Storage; serviços de inferência separados; banco de negócio; API e worker da aplicação; aprovação humana e integração via Hub.
3. **Referência funcional:** `REQ_InteligenciaeOtimizacaodeHorariosAcademicos_V4.4`, de 25/09/2026. Priorizar nesta POC: RGN001, RGN002, RGN003, RGN023; RF008–RF010, RF020–RF025, RF040–RF047, RF117–RF125 quando houver dados, RF155–RF159, RF195–RF199, RF204–RF206 e US016, US017, US022, US026–US030, US033–US034. Registrar explicitamente cobertura, simulação e itens não implementados.
4. **Decisão vigente de execução da POC:** Docker Compose (Windows/Docker Desktop e Linux quando suportado), não K3s/Rancher. Jupyter é **análogo funcional** ao futuro Workbench; RustFS é **análogo S3** do Object Storage futuro; PostgreSQL local é análogo ao armazenamento relacional futuro; não implementar GKE/GCP neste escopo.
5. **Precedência em conflitos:** regras funcionais V4.4 > hipótese ilustrativa; arquitetura V3 para alocação de responsabilidades-alvo > atalhos atuais da POC; código atual para compatibilidade e migração sem perda; este documento para novas correções. Registrar divergências antes de alterar contratos existentes. Não afirmar que payload de demonstração é contrato homologado da aplicação.

## 1. Objetivos e entregas obrigatórias

**Objetivo funcional:** provar, operando a partir do Jupyter, o ciclo **SQL/snapshot → preparação → treinamento efetivo → métricas, experimento e versão no MLflow/PostgreSQL → binário validável no RustFS → reload e inferência de versão explícita → composição de proposta de Planilha Turmas → persistência no PostgreSQL de negócio → consulta autenticada pela API → visualização/validação do mesmo payload que será entregue à aplicação**.

**Entregas:**

- Jornada existente `01_jornada_completa_planilha_turmas.ipynb` preservada e melhorada, sem quebrar a execução integral.
- **Novo** `notebooks/02_teste_inferencia_planilha_turmas.ipynb`: notebook independente para seleção de execução, chamada do endpoint da API, validação das regras/contrato, inspeção da proposta final, comparação API × banco × MLflow × RustFS e geração de relatório. Não deve treinar nem modificar propostas, salvo modo explicitamente opt-in e seguro para invocar inferência em ambiente DEMO, separado do fluxo de somente leitura.
- **Organização de notebooks científicos/operacionais** da seção 4.5, com notebooks de dados, treinamento individual, campanhas, avaliação, governança, inferência e reset total. O reset é operação destrutiva explicitamente opt-in, não rotina de teste automático.
- **Metodologia de rastreabilidade cross-system** com identidade canônica, tags/labels, manifesto versionado, links navegáveis e catálogo SQL de relações.
- **Contrato JSON versionado da proposta** com schema verificável e endpoint API para consultar representação consumida pela aplicação; se não houver contrato homologado, nomear `poc-planilha-turmas-v1` e sinalizar `PROVISÓRIO / PENDENTE DE HOMOLOGAÇÃO` em README, OpenAPI, notebook e relatórios.
- README estruturado (visão geral, arquitetura, quickstart, links de interfaces, jornada, modelo de 500+, rastreabilidade, API/payload, consultas, operação, troubleshooting e evidências), documentação de detalhes em `/docs`, sem listas de tecnologias ausentes.
- Testes unitários, de integração, E2E, contratuais e de invariantes; relatórios em `artifacts/reports/`; CI `development` com diagnóstico e correção do bloqueio MLflow unhealthy.
- Atualização das ADRs pertinentes e matriz de rastreio funcional/de responsabilidade IA × aplicação.

## 2. Separação clara de responsabilidades

| Camada | Responsabilidade | Escrita autorizada |
|---|---|---|
| Jupyter / Workbench | Experimentos, preparação, submissão e inspeção; coordenação DEMO da jornada | Runs/artefatos via MLflow; solicitações via APIs; no fluxo POC atual, composição/persistência demonstrativa de proposta com controle explícito |
| Training | Treinar modelos em processo efetivo, calcular métricas e identificar dataset/código | MLflow Tracking/Registry, RustFS via mecanismo MLflow e metadados de execução |
| MLflow | Experimentos/runs, métricas, tags, Registry, aliases e rastreabilidade do modelo | `mlflow_db` e artefatos no RustFS |
| RustFS | Snapshots, binários, manifests, hashes | Objetos versionados/imutáveis, nunca fonte de estado de aprovação |
| Inferência IA | Resolver versão aprovada ou explicitamente indicada em DEMO; carregar binário; prever | Logs, métricas e resultados da inferência (via contrato) |
| Planilha Turmas — POC | Compor resultado demonstrativo e persistir proposta original imutável | Schema `planning`, status técnico `DRAFT` |
| API Serviços Inteligentes | Expor inferências e contratos de consulta; autenticação | Resultados e protocolos conforme caso de uso |
| Aplicação / Worker (arquitetura-alvo) | Orquestração do ciclo acadêmico, regras transacionais, revisões, locks, aprovações, estados e publicação | Banco operacional da aplicação |

**Ponto a resolver formalmente com arquitetura/aplicação:** a POC atual escreve a proposta `DRAFT` diretamente a partir da jornada Jupyter; a arquitetura V3 apresenta o worker como coordenador de negócio. Nesta entrega, preservar a prova atual e definir uma interface/adaptador para futura transferência da responsabilidade sem acoplamento do contrato ao notebook. Não deslocar a escrita operacional definitiva sem alinhamento formal.

## 3. Metodologia de identidade e rastreabilidade: `HI-LINEAGE/1.0`

### 3.1 Princípios

- Um identificador tem **um único significado**; não reutilizar `run_id` para execução de negócio, nem versão do modelo para revisão da proposta.
- **Chaves canônicas obrigatórias**, compatíveis com PostgreSQL/MLflow/JSON/logs/manifestos, em `snake_case`; informações extensas em tabelas e manifestos, tags curtas como índice de navegação.
- Modelo tem identidade estável; **run** é uma execução de treino; **versão** é uma versão registrada; **snapshot** é o insumo imutável; **inference_id** identifica inferência; **proposal_id** identifica a proposta de negócio; **proposal_revision** distingue revisões posteriores humanas sem modificar a proposta original.
- A cardinalidade é **N:N** quando aplicável: uma proposta pode usar resultados de vários modelos/versões e um modelo pode produzir diversas previsões/propostas. Não presumir `proposal → exatamente 1 model_version` em arquitetura de 500+ modelos.
- Use **UUID/ULID gerado uma vez**, com IDs externos preservados conforme origem. **Não derivar ID apenas do timestamp**. ISO-8601 UTC em todos os eventos.
- Nada confidencial em tags, nomes de objetos, URLs, traces, relatórios ou outputs de notebooks. Credenciais ficam em `.env`/secrets, redigidas em logs.
- SHA-256 para integridade de snapshot, binário, manifesto e payload normalizado; distinguir hash de dataset, hash de pacote e hash de resposta JSON.

### 3.2 Dicionário mínimo de identidades

| Campo | Escopo / significado | Exemplo DEMO |
|---|---|---|
| `solution_id` | Solução | `horarios-inteligentes` |
| `environment` | Ambiente lógico | `poc` (`dev`, `qa`, `uat`, `prd` no futuro) |
| `domain` | Produto | `planilha-turmas` |
| `academic_cycle_id` / `cycle_code` | Ciclo alvo | UUID / `2027-1` |
| `snapshot_id` | Dataset imutável de entrada | UUID real do snapshot |
| `snapshot_sha256` | Integridade do snapshot/manifest | SHA-256 hex |
| `model_key` | Identidade funcional estável | `C1-CR1-P1` (convenção atual, não renomear silenciosamente) |
| `experiment_id` | Contêiner lógico MLflow | ID MLflow |
| `run_id` | Execução de treinamento MLflow | ID MLflow |
| `registered_model_name` | Nome no Registry | nome completo existente |
| `model_version` | Versão no Registry do modelo | string/int de MLflow |
| `artifact_uri` | Local canônico do artefato no MLflow | URI retornada pelo MLflow |
| `artifact_sha256` | Digest do binário/pacote | SHA-256 |
| `code_version` | Hash/commit do código efetivamente executado | commit SHA ou hash reproducível |
| `config_hash` | Hash config de treinamento | SHA-256 |
| `training_campaign_id` | Agrupamento de centenas de treinos | UUID opcional por campanha |
| `inference_id` | Uma invocação/snapshot de inferência | UUID |
| `proposal_id` / `execution_id` | Instância da proposta / jornada (manter alias existente) | UUID |
| `proposal_revision` | Revisão da proposta no domínio | 1, 2, ... |
| `schema_version` | Contrato do payload | `poc-planilha-turmas-v1` |
| `correlation_id` / `trace_id` | Observabilidade de chamada | IDs independentes |
| `ruleset_version` / `ruleset_hash` | Versão das regras demonstrativas usadas | `demo-rules-v1` e SHA-256 |

**Compatibilidade:** reconciliar `dataset_sha256` e `snapshot_sha256` conforme semântica real do código; não substituí-los cegamente — podem representar hashes distintos (extração tabular vs snapshot/manifests). Documentar mapeamento. `execution_id` já é usado como identificador da proposta na jornada; preservar o contrato existente e expor `proposal_id` como alias quando útil.

### 3.3 Tags MLflow obrigatórias e política de cardinalidade

**Nas runs de treinamento:** `solution_id`, `environment`, `domain`, `academic_cycle_id`, `snapshot_id`, `snapshot_sha256` (ou `dataset_sha256` com mapeamento), `model_key`, `training_campaign_id` (quando houver), `code_version`, `config_hash`, `algorithm`, `source_type` (`DEMO`/`INSTITUTIONAL`), `ruleset_version` quando relevante. Run ID e experiment ID são campos nativos MLflow e não precisam ser duplicados; colocar seus links no manifesto.

**No Model Registry/versão:** `model_key`, `snapshot_id`, `run_id`, `code_version`, `artifact_sha256`/`bundle_sha256`, `schema_version`, `source_type`, `validation_status`; aprovação/alias deve ser consistente com a tabela auditável `model_deployments`. Tags são **índices auxiliares**, não fonte única da decisão de aprovação.

**Nos experimentos:** nome e descrição estáveis por domínio/família ou campanha; jamais um experimento obrigatório por modelo. Exemplo: `hi/poc/planilha-turmas/demanda` e opcional `hi/poc/planilha-turmas/campaign-<id>`. Respeitar nomes/IDs já existentes, mantendo compatibilidade histórica.

**Nos traces:** `correlation_id`, `execution_id`, `inference_id` quando houver, `model_key`/versão ou `campaign_id` (se múltiplos), etapa e tentativa; não capturar payload acadêmico identificável por padrão. Não empilhar listas extensas de 500 versões em tags; use tabela relacional/manifesto.

### 3.4 Layout do storage e metadados

Preservar os caminhos atuais do MLflow, inclusive prefixo `pucpr-poc/mlflow/`, pois o MLflow controla URIs e links de versões. **Não reescrever manualmente caminhos de artefatos do Registry.** Acrescentar manifestos auxiliares com layout lógico sugerido:

```text
pucpr-poc/
  mlflow/...                           # localização controlada por MLflow
  snapshots/<snapshot_id>/manifest.json
  lineage/<environment>/<domain>/
    campaigns/<training_campaign_id>/manifest.json
    proposals/<proposal_id>/revisions/<revision>/manifest.json
    inferences/<inference_id>/manifest.json
```

Cada manifesto JSON deve ter `manifest_schema_version`, `created_at_utc`, os IDs canônicos pertinentes, hash do conteúdo e ligações por ID/URI ao resto da cadeia. Endereço físico do objeto **não é chave de negócio**, e ambiente deve ser segmentado por credencial/bucket/prefixo conforme contrato de implantação. Proibir segredos e dados pessoais no manifesto. Implementar escrita idempotente: se objeto existe com mesmo hash, aceitar; se conteúdo difere, falhar sem sobrescrever.

**Provar object store:** acessar RustFS S3 diretamente (`head/get_object`), comparar hash do binário com download pelo MLflow, carregar o modelo e confirmar previsões. Se `bucket versioning` não estiver habilitado, não declarar suporte a versões nativas S3; versionamento semântico ocorre pelo Registry + manifests imutáveis.

### 3.5 Modelo relacional para lineage (migrações ADITIVAS)

Inspecionar primeiro `sql/ddl/001_planning.sql`, `002_immutability.sql`, `004_journey.sql`, migrations Alembic e tabelas existentes. **Não criar duplicidades**. Acrescentar as relações faltantes com migration seguinte, sugerida `005_lineage_contract` (ajustar ao head real). Campos a implementar ou mapear para equivalentes:

- `planning.lineage_entities`: `(entity_id UUID PK, entity_type, external_id, environment, domain, created_at_utc, attributes JSONB)`; UNIQUE `(entity_type, environment, external_id)`.
- `planning.lineage_edges`: `(edge_id UUID PK, parent_entity_id FK, child_entity_id FK, relation_type, created_at_utc)`; UNIQUE por tripla; relações `DERIVED_FROM`, `TRAINED_ON`, `REGISTERED_AS`, `PREDICTED_WITH`, `CONTRIBUTED_TO`, `EXPOSED_AS`, `REVISED_FROM`.
- `planning.proposal_model_usage`: relação explícita **N:N** entre proposta/linha/inferência e `model_key + registered_model_name + model_version + run_id + snapshot_id`, com `artifact_sha256`/`ruleset_hash` quando aplicáveis. Índices por `proposal_id`, `model_key`, `run_id`, `snapshot_id`.
- `planning.proposal_contract_evidence`: `(proposal_id, proposal_revision, schema_version, payload_sha256, published_at_utc, row_count, validation_status, validation_report_uri, created_at_utc)`; UNIQUE `(proposal_id, proposal_revision, schema_version)`.
- Reutilizar tabelas atuais (`dataset_snapshots`, `training_executions`, `model_catalog`, `model_deployments`, `proposal_generations`, `proposal_lines`, `audit_events`) como fontes relacionais, com FKs e views para consulta intuitiva. Preferir **views** às tabelas espelho quando dados já estão integralmente presentes.

**Restrições:** índices, chaves únicas, FKs apropriadas, idempotência, `NOT NULL` onde possível sem quebrar legado, transações e preservação do histórico. `audit_events` append-only; testes de tentativa de UPDATE/DELETE negados. Não acoplar app DB ao schema interno do MLflow via FK cross-database: armazenar referências externas e validar via SDK/API do MLflow. Não armazenar binário no PostgreSQL.

### 3.6 Consultas e navegação intuitiva

Criar `sql/queries/lineage_by_proposal.sql`, `lineage_by_model.sql`, `lineage_by_snapshot.sql`, `lineage_by_run.sql` e, se necessário, `planning.v_lineage_proposal` para retornar cadeia única:

`ciclo → snapshot/hash → campanha → run/experimento → model_key/versão → artefato URI/hash → inferência → linha(s) da proposta/revisão → evidência API/schema → status`.

Adicionar endpoint **somente leitura e autenticado**, por exemplo `GET /v1/proposals/{execution_id}/lineage`, com links relativos e IDs. Para 500 modelos, paginação e filtros; não devolver milhares de referências por padrão. Status de ausência/inconsistência visível; nunca fabricar link/URI. Dashboard/README devem mostrar como sair de `proposal_id` até MLflow e RustFS, e vice-versa.

## 4. Notebook `02_teste_inferencia_planilha_turmas.ipynb`

### 4.1 Papel e premissas

Notebook de **verificação do artefato consumido pela aplicação**, independente do notebook de treino. Recebe como parâmetros `API_BASE_URL`, `API_TOKEN` (somente via env/secret), `execution_id` ou seleção controlada da proposta DEMO, `cycle_code`, `expected_schema_version` e `validation_profile` (`demo` ou `v44_partial`). Deve consumir endpoint HTTP real autenticado, não chamar função Python de montagem da proposta no lugar da API. Saída principal é a **estrutura JSON exatamente como o cliente aplicação receberá**, além de uma visão tabular legível e relatório de conformidade.

**Não confundir:** consultar uma proposta persistida (`GET`) é diferente de iniciar uma inferência (`POST`). Implementar **duas rotas explícitas** no notebook: (A) consulta/read-only de proposta existente (padrão); (B) teste opcional de inferência explícita para gerar novo resultado DEMO com modelo/versão/snapshot conhecidos, sem promoção, sem escrita em fontes institucionais e com indicador `DEMO`. Nunca executar POST na inicialização automática do notebook.

### 4.2 Células/seções obrigatórias

1. **Capa operacional:** objetivo, versão do notebook, branch/commit, data UTC, arquitetura e advertência DEMO/contrato provisório.
2. **Configuração:** endpoints, token via env, `execution_id`, ciclo, paginação, timeout, quantidade máxima de linhas e perfil de validação. Exibir valores sanitizados (nunca token).
3. **Preflight:** health/readiness da API, autenticação positiva/negativa, OpenAPI disponível, existência da proposta; mensagens PASS/FAIL acionáveis.
4. **Seleção da proposta:** `GET /v1/proposals` filtrado por ciclo ou ID configurado; escolher uma geração sem depender de “última” aleatória; imprimir `execution_id`, status, snapshot, run, versão, data.
5. **Consulta canônica:** `GET /v1/proposals/{execution_id}` e `GET /v1/proposals/{execution_id}/lines` com paginação até reconciliar todas as linhas (ou endpoint JSON único de contrato definido adiante). Rejeitar perda de linhas, duplicação ou paginação incompleta.
6. **Payload final:** chamar endpoint canônico `GET /v1/proposals/{execution_id}/application-view` (a implementar **sem quebrar endpoints antigos**) e mostrar JSON íntegro, validado com JSON Schema/Pydantic. Exibir resumo, tabela de ofertas e grupos, distribuição por tipo de aluno, regras aplicadas, status/pendências; campos ausentes não podem ser preenchidos silenciosamente.
7. **Validação funcional:** verificar as regras V4.4 aplicáveis ao perfil selecionado, com ID `RGN`/`RF`/`US`, decisão `PASS`/`FAIL`/`NOT_EVALUATED`, motivo e evidência. Não marcar regra como PASS se o dataset DEMO não contiver as entradas necessárias.
8. **Prova de linhagem:** obter `GET .../lineage`, checar MLflow por SDK/HTTP, Registry, run, versão, artefato RustFS e SQL read-only independente; verificar hashes e referências.
9. **Comparação contrato × SQL × API:** confrontar número de linhas, chaves de negócio, quantidades, tipos numéricos, status, IDs, payload hash; erro explícito em divergência.
10. **Teste negativo controlado:** token inválido → 401/403; proposta inexistente → 404; schema incompatível → falha; `model_version`/hash divergente → falha; proposta sem evidência de origem → falha. Não alterar produção/dados reais.
11. **Relatório final:** tabela por etapa PASS/FAIL/NÃO AVALIADO; IDs, URLs locais úteis, métricas, evidência do payload validado, hashes, limitações e local do relatório. Salvar em `artifacts/reports/inference-contract-<execution_id>.json` e `.md` (sem credenciais/PII); saídas versionáveis determinísticas quando possível.

### 4.3 Payload de aplicação versionado (EXEMPLO DE CONTRATO PROPOSTO)

**Atenção:** o exemplo abaixo é proposto para validação da POC; não consta como contrato final homologado no material fornecido. Negociar campos definitivos com a equipe de Aplicação/IA; disponibilizar documentação OpenAPI e schema em `docs/contracts/planilha-turmas-poc-v1.schema.json`. Preservar `GET /v1/proposals` e `/lines` existentes.

```json
{
  "schema_version": "poc-planilha-turmas-v1",
  "proposal_id": "<uuid>",
  "execution_id": "<uuid>",
  "proposal_revision": 1,
  "academic_cycle": { "cycle_id": "<uuid>", "cycle_code": "2027-1" },
  "status": "DRAFT",
  "source_type": "DEMO",
  "generated_at_utc": "2026-11-04T12:00:00Z",
  "lineage": {
    "snapshot_id": "<uuid>",
    "snapshot_sha256": "<sha256>",
    "training_campaign_id": null,
    "ruleset_version": "demo-rules-v1",
    "model_usages": [
      {
        "model_key": "C1-CR1-P1",
        "registered_model_name": "planilha-turmas-demo",
        "model_version": "8",
        "run_id": "<mlflow-run-id>",
        "artifact_sha256": "<sha256>"
      }
    ]
  },
  "offers": [
    {
      "offer_id": "<stable-offer-id>",
      "campus_id": "<id>",
      "course_id": "<id>",
      "discipline_id": "<id>",
      "period_id": "<id>",
      "shift": "NOTURNO",
      "offer_type": "REGULAR",
      "offer_status": "SUGERIDA",
      "students": {
        "regular": 40,
        "dependency": 5,
        "elective": 8,
        "total": 53,
        "regular_origin": "SOURCE",
        "irregular_origin": "HISTORICAL_ESTIMATE"
      },
      "modulation": {
        "max_students_per_group": 30,
        "proposed_groups": 2,
        "groups": [
          { "group_code": "G1", "students": 27 },
          { "group_code": "G2", "students": 26 }
        ]
      },
      "teacher_suggestion": null,
      "warnings": [],
      "source_model_keys": ["C1-CR1-P1"]
    }
  ],
  "validation": {
    "profile": "demo",
    "rules_evaluated": ["RF008", "RF009", "RF023", "RF025"],
    "rules_not_evaluated": ["RF054", "RF117"]
  }
}
```

Valores acima são **ilustrativos**, não extraídos da POC. O endpoint real deve retornar dados existentes, sem inventar professor, modulação ou campos desconhecidos. Se uma propriedade não puder ser fornecida no dataset DEMO, permitir `null`, `NOT_EVALUATED` ou omissão conforme schema documentado — nunca atribuir um valor simulado sem sinalização.

### 4.4 Regras aplicáveis e critérios verificáveis

**Roteiro de validação extraído da V4.4:**

- **RGN001 / US027:** a proposta é sugestão; não simular aprovação acadêmica nem publicar automaticamente.
- **RGN023 / US028:** na primeira fase, gerar disciplinas da matriz/estimativas, com gate de validação para fases seguintes. A POC pode testar somente fase inicial; deve identificar explicitamente o estágio.
- **RF008–RF009 / US027:** oferta regular inicialmente sem alocação docente, horário e sala. `teacher_suggestion` só pode ser preenchido na etapa subsequente, quando suportada.
- **RF020 / US026:** identificação de turma por curso e semestre/ano de ingresso quando dados disponíveis.
- **RF021–RF025 / US029–US030:** separar regulares dos adicionais, somar totais coerentes, conservar origem direta vs estimativa histórica.
- **RF040–RF047 / US033–US034:** modulação e número de grupos precisam respeitar regras da matriz e sequência após unificações, quando as entradas necessárias existirem. **Não aplicar indiscriminadamente o `capacity=40` DEMO como regra institucional.**
- **RF117–RF125:** unificação requer elegibilidade e processo/validação, e não pode ser confirmada automaticamente pela POC.
- **RF155–RF159 / US005–US006:** fonte histórica com referência temporal; não escrever no PRIME nem executar matrículas.
- **RF195–RF199 / US016:** eventos, autoria, estado, justificativa, rastreabilidade e imutabilidade.
- **RF204–RF206 / US017:** preservar sugestão original, distinguir ajustes e resultados humanos validados; não usar decisões intermediárias como feedback automático.

O status técnico de geração `DRAFT` não substitui o estado funcional da oferta (`SUGERIDA`/`EDITADA`/`PENDENTE`/`APROVADA`). Mantê-los como campos distintos. Nesta POC a atualização humana não precisa ser implementada; os registros precisam estar preparados para não sobrescrever o original.

## 4.5 Catálogo de notebooks e organização do ambiente científico

**Objetivo:** colocar o JupyterLab (futuro Vertex AI Workbench) como interface única do cientista, sem duplicar notebook por modelo. O notebook principal já implementado deve permanecer **inalterado no nome e executável de ponta a ponta**. Os demais devem chamar funções reais reutilizáveis de `src/` e APIs; não duplicar o algoritmo em células. Adotar a seguinte organização, com README e links para cada notebook:

| Ordem | Notebook | Papel e resultado verificável | Operação |
|---|---|---|---|
| 00 | `00_validacao_ambiente.ipynb` | Preflight: serviços, endpoints, SQL, MLflow, RustFS, permissões, versões, saúde e relatório PASS/FAIL | Somente leitura + diagnósticos seguros |
| 01 | `01_jornada_completa_planilha_turmas.ipynb` | Prova ponta a ponta vigente: SQL → treino → MLflow → RustFS → inferência → proposta → PostgreSQL → API | Escreve dados DEMO, preserva funcionamento atual |
| 02 | `02_teste_inferencia_planilha_turmas.ipynb` | Aciona inferência DEMO opcional, lê API final, valida payload, regras e linhagem, compara API/SQL/MLflow/RustFS | Leitura padrão; POST só com opt-in |
| 03 | `03_exploracao_preparacao_dados.ipynb` | Dados, qualidade, snapshots, período temporal, features e evidências de origem | Leitura padrão; snapshot controlado |
| 04 | `04_treinamento_individual.ipynb` | Escolher `model_key`, snapshot, algoritmo/config; treinar, metrificar, registrar run e versão candidata | Treino explícito |
| 05 | `05_treinamento_campanha.ipynb` | Submeter/acompanhar lote de N modelos por `training_campaign_id`, concorrência limitada, retry e retomada | Jobs explícitos; não rodar 500 automaticamente |
| 06 | `06_avaliacao_comparativa.ipynb` | Comparar métricas/backtesting, dados, versões e candidatos sem promoção implícita | Somente leitura |
| 07 | `07_registry_governanca.ipynb` | Conferir origem, artefatos, versão e estado; demonstrar aprovação/publicação com operador e justificativa | Leitura padrão; aprovar/promover somente com comando explícito e registro auditável |
| 08 | `08_auditoria_lineage.ipynb` | Pesquisa bidirecional por proposta, run, modelo, versão, campanha ou snapshot; links MLflow/RustFS/SQL/API | Somente leitura |
| 09 | `09_reset_total_ambiente_poc.ipynb` | Inventariar, pré-visualizar e, após confirmação forte, coordenar limpeza completa e verificar ambiente vazio/reinicializável | **Destrutivo somente com confirmação** |

**Importante:** não renomear nem deletar notebook fonte atual ou workspace do cientista. O notebook 00 não deve substituir a jornada 01; o 02 continua sendo o notebook da visão final entregue à aplicação. Na inicialização do Jupyter, publicar arquivos novos de forma **não destrutiva**: não sobrescrever arquivos já editados em `/workspace/notebooks`; usar sincronização com check de hash ou cópia com sufixo de versão em caso de conflito. Navegação sugerida: `notebooks/README.md` com links, objetivos, pré-requisitos, operações que geram escrita e evidências. Se a implementação dos notebooks 03–08 exigir APIs ainda não prontas, implementar incrementos mínimos ou marcar os trechos como `NOT_IMPLEMENTED` sem criar notebooks decorativos que simulam sucesso.

## 4.6 Notebook de reset total e limpeza controlada da POC

**Motivação:** em testes periódicos será necessário voltar a uma POC zerada, inclusive modelos registrados, runs/experimentos e traces MLflow, objetos RustFS, snapshots, propostas, auditoria de demonstração e bancos PostgreSQL. O mecanismo deve ser explícito, reproduzível, verificável e incapaz de afetar outros projetos/ambientes. Implementar o notebook `09_reset_total_ambiente_poc.ipynb` e um **orquestrador externo** `deployment/scripts/reset_poc.ps1` + `reset_poc.sh`, ou um CLI de reset equivalente invocado por estes scripts. O código de operação destrutiva deve ser único, testável e reutilizado pelo notebook, não espalhado em células SQL.

### 4.6.1 Modos distintos

- **`preview` (padrão e sem escrita):** obter inventário com data UTC, projeto Compose detectado, containers, volumes nomeados, bancos, schemas, modelos, versões, experimentos, runs, traces, quantidade de propostas/snapshots, objetos RustFS por prefixo, RabbitMQ e espaços de workspace/logs. Mostrar exatamente o que será apagado e o que será preservado, com `plan_id` e `plan_sha256`.
- **`reset-data`:** esvaziar apenas dados de negócio sintéticos, modelos/experimentos da POC e seus objetos, filas e evidências temporárias da POC, mantendo imagens/configurações e stack operacional. Deve ser implementado como processo controlado, parando consumidores/escritores e com reconciliação; **não presumir que apagar algumas tabelas MLflow manualmente seja seguro**. Se não houver mecanismo suportado para limpeza confiável de seu backend, preferir recriar banco MLflow dedicado e artefatos da POC, mantendo configuração.
- **`factory-reset`:** apagar **todos os dados persistentes de serviços exclusivos da POC** e recomeçar como primeira instalação: bancos `planejamento_db` e `mlflow_db`, respectivos roles somente se forem exclusivos e inequivocamente identificados, MLflow Tracking/Registry/runs/traces, artefatos e snapshots RustFS da POC, volumes dedicados de PostgreSQL/RustFS/RabbitMQ, estado dos modelos publicados, cache e runtime gerado. Containers e volumes dedicados podem ser recriados pelo bootstrap. **Não tocar no `.env`**, tokens, fontes de referência Git, arquivos pessoais do workspace ou backups anteriores. Para workspace/relatórios/logs: permitir flag **separada** `--include-generated-files`, com inventário e proteção de notebooks editáveis. Nenhum modo deve apagar arquivos pessoais `Untitled`, notebooks editados, arquivos externos, projetos irmãos ou recursos GCP.

### 4.6.2 Proteções obrigatórias

1. **Bloqueio de ambiente:** recusar se `environment != poc`, se contexto for GKE/PRD, se o projeto Compose/diretório não corresponder a uma allowlist explícita (ex.: `marista` + assinatura da POC), se os bancos/buckets/volumes não forem exclusivamente da POC ou se o escopo não puder ser demonstrado. Verificar recursos efetivos do Compose com labels, `docker compose config`, volume names, endpoints e variáveis, e não confiar só no nome digitado.
2. **Pré-visualização:** mostrar inventário com quantidades e nomes de recursos, totais por namespace de dados e plano de exclusão. Exportar `artifacts/reports/reset/preview-<plan_id>.json` sanitizado. Aguardar decisão humana; não permitir exclusão disparada por import de módulo, `Run All` simples, CI ou inicialização do Jupyter.
3. **Confirmação dupla:** exigir `plan_id` válido, hash ainda atual, `--execute` explícito no script e uma frase de confirmação específica digitada pelo operador, por exemplo `APAGAR TODOS OS DADOS DA POC MARISTA`; `force`, `yes` genérico, checkbox pré-marcado e variáveis CI não são confirmação suficiente. Planos expiram se inventário ou assinatura de escopo mudarem.
4. **Sessão Jupyter:** como `factory-reset` interromperá PostgreSQL, MLflow, RustFS e possivelmente o próprio Jupyter, **não prometer acompanhar até o fim no kernel que será destruído**. O notebook 09 monta/mostra o plano, gera identificadores e instrui ou dispara um controlador externo seguro. Esse controlador independente deve registrar progresso e completar validação; se não houver mecanismo confiável para acioná-lo de dentro do notebook, apresentar o comando exato para execução no terminal do host, sem alegar que foi executado.
5. **Quiescência:** pausar API, worker, training, inferência, ingestion e jobs antes de limpar; verificar que não há writes/training pendentes. Usar locks e exclusão coordenada. `docker compose down -v` **só pode ser usado dentro do factory-reset** após validação estrita de que o projeto e volumes são exclusivos; não usar `docker volume prune`, `docker system prune`, `docker rm -f $(...)` indiscriminado, `DROP DATABASE` em instância compartilhada, remoção global de buckets ou limpeza de prefixos não pertencentes à POC.
6. **Backups:** informar claramente irreversibilidade e oferecer backup/export **opcional e explícito** antes da exclusão; para esta POC, permitir reset sem backup quando houver confirmação forte, mas nunca sobrescrever ou apagar backups antigos. Não exportar segredos para relatórios.
7. **Auditoria e retomada:** persistir plano/resultado em relatório local **fora dos volumes apagados**, com data, operador, commit, recursos, operações, contagens antes/depois e status de cada etapa. Uma falha parcial deve interromper o fluxo, identificar recursos já apagados e permitir retomada idempotente somente após revalidar o plano; não reportar `PASS` parcial.
8. **Testes:** dry-run sem mudança; recusa em `dev/qa/uat/prd`; recusa de escopo externo; recusa sem frase; recusa de plano alterado; falha durante limpeza; reinicialização idempotente em stack descartável; nenhuma rotina destrutiva rodando no ambiente de desenvolvimento atual. Usar CI descartável isolada exclusivamente para testar o reset (com volumes/buckets/bancos temporários) e nunca reutilizar volumes de usuário.

### 4.6.3 Fluxo operacional esperado

```text
Jupyter 09 → Preflight & inventário → PREVIEW (sempre)
           → operador escolhe reset-data ou factory-reset
           → confirmação forte vinculada ao plan_id
           → controlador externo isolado para writers/containers
           → exclusão por escopo validado
           → reconstrução/bootstrapping opcional (--reinitialize)
           → verificação independente de estado zerado
           → relatório RESET_PASS / RESET_FAILED / RESET_PARTIAL
```

No `factory-reset --reinitialize`, reinicializar instância SQL, roles e bancos exclusivos, schemas Alembic e MLflow, bucket dedicado e serviços. **A semântica de “zerado” deve ser selecionável:** `empty` (sem seed sintético, runs ou propostas) e `demo-ready` (serviços ativos e dados DEMO re-semeados, mas sem treinos, versões ou propostas). Registrar exatamente quais dados foram reintroduzidos. `reset-data` e `factory-reset` não devem promover modelos automaticamente.

### 4.6.4 Verificações obrigatórias pós-reset

- **MLflow:** zero experimentos/runs/modelos/versões **da POC** (exceto eventual experimento `Default` nativo vazio) e zero traces da POC; checar pelo SDK/API e banco dedicado quando aplicável.
- **RustFS:** nenhum objeto da POC nos prefixos `mlflow/`, `snapshots/`, `lineage/`, `backups-temporarios/` quando este último for explicitamente dedicado; preservar backups externos/anteriores e outros buckets.
- **PostgreSQL:** banco/schema reinicializado ou vazio conforme modo, zero propostas, linhas, predições, execuções e snapshots DEMO; verificar com conexão SQL independente. Se `demo-ready`, permitir somente tabelas de catálogo e seed esperados, com contagens declaradas.
- **RabbitMQ/model runtime:** filas da POC vazias, nenhuma publicação/alias/serviço dinâmico de modelo sobrevivente, nenhum cache de modelos antigo; verificar endpoint e inventário Docker.
- **Jupyter/arquivos:** notebook fonte e workspace editável preservados, novo preflight utilizável, `.env` e scripts intactos, evidência de reset em pasta persistente fora do escopo. O notebook 09 mostra como abrir os relatórios após o restart.
- **Smoke pós-bootstrap:** `00_validacao_ambiente.ipynb` pronto para PASS; `01_jornada_completa_planilha_turmas.ipynb` pode ser reexecutado como uma primeira jornada, sem resíduos de runs/artefatos/propostas anteriores; se executado, registrar uma nova campanha/jornada distinta.

### 4.6.5 README e operações

Criar `docs/operations/RESET_POC.md` com escopo, tabela recursos apagados/preservados por modo, comando `preview`, exemplos de `--execute` com placeholders (nunca autoexecutáveis), comando de status, log, exemplos `--reinitialize empty|demo-ready`, roteiro de recuperação em falha parcial e evidências do zero. Incluir seção visível no README **“Reset total da POC — operação destrutiva”** e link para Notebook 09. Não colocar reset como etapa do quickstart, `make test`, `acceptance`, `rebuild`, `git push` ou CI comum.

## 5. 500+ modelos: governança, organização e testes

- **Um JupyterLab é interface do cientista, não instância obrigatória por modelo.** Manter notebook central de aceite e adicionar notebook de inferência; scripts Python reutilizáveis. Treinamentos escaláveis devem ser jobs em lote sob concorrência controlada, não 500 notebooks duplicados nem 500 processos vivos permanentes por padrão.
- MLflow: **experimento por domínio/família/campanha**, runs individuais por treino, Registry por chave de modelo estável e versões sob cada chave. Não gerar 500 experimentos como obrigação nem colapsar 500 modelos distintos em um único modelo registrado sem identidade própria.
- Propor `training_campaign_id` com tabela de itens e estados (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `SKIPPED`), backoff, retry idempotente, checkpoint/restart, limites de concorrência configuráveis, métricas agregadas e inventário no README. Implementação do mecanismo de campanha deve ser incremental e não bloquear o aceite básico.
- Criar testes com 1 modelo (jornada completa), 30 modelos (lote) e **500 identidades de modelo** (inventário, tags, relacionamentos, storage e consultas). Diferenciar com clareza: *500 modelos registrados*, *500 treinos executados*, *500 APIs publicadas* e *500 modelos carregados simultaneamente* são ensaios distintos. Não afirmar benchmark de capacidade sem executar carga/medir CPU, RAM, tempo e taxa de erros.
- Distinguir publicação por API dedicada (código atual) vs serving por pool/router com lazy load + cache (hipótese de evolução). Não criar automaticamente 500 containers por registrar 500 modelos; documentar trade-offs e fazer spike limitado, sem alterar C3 institucional sem aprovação.

## 6. README e documentação operacional

Reescrever/organizar o `README.md` existente para **ser a porta de entrada única**. Índice recomendado:

1. Contexto, objetivo e limites da POC; referência aos desenhos V3 e requisitos V4.4.
2. Diagrama arquitetural claro (mermaid) com treinamento, inferência, persistência e consulta API; indicar equivalências Compose ↔ futuro GCP.
3. Inventário de componentes, papéis, bancos, buckets, DNS/portas e credenciais via `.env` (nunca imprimir valor secreto).
4. Quickstart Windows/PowerShell e Linux/Bash com pré-requisitos, comandos reais existentes e verificados, build, init, start/status, stop, logs, rebuild sem destruir volumes.
5. Índice dos notebooks `00`–`09`, com propósito, nível de permissão, ordem recomendada e localização das evidências.
6. Jornada 01 completa com células, ordem, dependências, resultados e links MLflow/RustFS/Postgres/API. Jornada 02: como selecionar proposta, opcionalmente invocar nova inferência DEMO, consumir payload de aplicação, validar regras e exportar evidências.
7. Metodologia `HI-LINEAGE/1.0`: tabela de IDs, convenção de tags, nomes, manifestos, esquema relacional, consultas e exemplos bidirecionais.
8. MLflow: experimentos, runs, Model Registry, versões, aliases e política de aprovação; explicação de 500 modelos sem 500 Jupyters.
9. RustFS: acesso, bucket, localização dos artefatos e verificação de SHA-256.
10. PostgreSQL: dois bancos lógicos, schema `planning`, DDL/migrations, consultas de auditoria e lineage.
11. Contrato API da proposta: Swagger, exemplos válidos, paginação, autenticação, schema, relação com status e limites da cobertura funcional.
12. Reset total da POC (`09_reset_total_ambiente_poc.ipynb`), modos preview/reset-data/factory-reset, proteção de escopo, confirmação e reinicialização.
13. Aceite, evidências, testes negativos, CI, troubleshooting, dashboards e limitações.

Criar/atualizar `docs/architecture/LINEAGE.md`, `docs/contracts/README.md`, `docs/operations/INFERENCE_NOTEBOOK.md`, `docs/operations/MLFLOW_MODEL_ORGANIZATION.md` e, se necessário, uma ADR curta para contratos/identificadores. Links relativos válidos; diagramas compatíveis com GitHub; remover instruções operacionais contraditórias em documentos atuais sem apagar histórico de decisões.

## 7. CI e segurança de execução

O workflow `/.github/workflows/compose.yml` na `development` está falhando no estágio **Build and provision dependencies**: MLflow reportado `unhealthy` após PostgreSQL/RustFS/RabbitMQ `healthy`. Antes de corrigir por tentativa:

1. Reproduzir em ambiente descartável/isolado; coletar **logs do container MLflow**, `docker compose ps`, inspect de saúde, comando de startup, resultado `mlflow db upgrade`, DNS, credenciais de CI (sem valores), readiness, timeout e conexões DB/S3.
2. Identificar causa raiz e corrigir de forma mínima; se for startup/migration lenta, adequar probes/start-period a evidências, sem mascarar falha de schema/credenciais.
3. Em falha, capturar diagnósticos sanitizados como artifact do GitHub Actions **antes** de `down -v` no ambiente descartável; nunca fazer limpeza de volumes persistentes de desenvolvimento.
4. `development` CI deve passar build, bootstrap, migrations, seed, jornada Jupyter, testes, verificação de proposta e contrato da API. CI deve registrar em artifacts o resumo verificável.
5. Evitar token no notebook, hash/URI secreto no log, dados pessoais nos traces e acessos externos sem autenticação. Documentar que MLflow local pode ficar sem auth HTTP apenas restrito ao loopback; não inferir segurança equivalente em PRD.

## 8. Plano de implementação em ordem obrigatória

**Fase A — Diagnóstico, sem mudanças:** capturar SHA da branch, árvore relevante, serviços, endpoints reais, tabelas, colunas e migrations. Inspecionar notebook e payload atual, produzir matriz `existente × ajuste necessário × regra V4.4`. Apontar incompatibilidades de nomes/campos e estratégia de backward compatibility.

**Fase B — Identidades:** criar módulo central (sugestão: `src/common/lineage.py`) com modelos tipados, hashes JSON canônicos, validação de UUID/ID, normalização de tags e gerador de manifestos, sem depender de UI. Testes de serialização, determinismo e prevenção de dados sensíveis.

**Fase C — Persistência:** migrações aditivas, índices, views e consultas de lineage; backfill seguro do histórico apenas quando IDs/hash existentes forem suficientes; identificar dados legados com `UNKNOWN`/ausência em vez de inventar. Não tocar nas tabelas internas do MLflow.

**Fase D — Propagação:** integrar identidades no SQL/snapshot, training, MLflow tags e Registry, RustFS manifests, inferência, proposta, API, logs e tracing; testes integrados verificando mesma identidade em todos os sistemas. Manter CLI/scripts existentes.

**Fase E — Contrato de aplicação:** definir JSON Schema provisório, Pydantic, endpoint `application-view`, serialização determinística, status/erro, paginação quando aplicável, headers de correlação e OpenAPI; checar respostas com banco. Requisitos não cobertos devem ser sinalizados.

**Fase F — Catálogo de notebooks 00–09:** criar/notabilizar notebooks por função segundo seções 4.5–4.6, com implementação não decorativa e funções reutilizadas de `src/`; implementar o reset e scripts de modo seguro, mas **não executar reset real nesta entrega**. **Notebook 02:** desenvolver notebook legível, parametrizável, read-only por padrão, com API real, validação funcional, lineage, SQL/storage/MLflow e evidências; gerar cópia editável no Jupyter sem sobrescrever notebook pessoal preexistente. Atualizar `src/common/launch.py` com mecanismo seguro de distribuição de notebooks novos sem clobber.

**Fase G — Organização multi-modelo:** convenções MLflow, inventário por modelo/campanha, testes 30/500 conforme recursos; não introduzir orquestrador novo sem justificativa e validação do escopo.

**Fase H — README e docs:** documentar explicitamente `RESET_POC.md`, os dez notebooks e seus níveis de risco; consolidar material com comando único de aceite e mapa de navegação completo. Revisar documentação histórica de Kubernetes para que não pareça runtime vigente.

**Fase I — Aceite e CI:** testes reais, falhas induzidas, restarts/rebuild sem perda, pipeline Github e relatório consolidado; não fazer push/merge ou ações destrutivas sem instrução explícita. Caso ambiente Docker não esteja disponível, executar análise estática e marcar testes reais `NOT_EXECUTED` com motivo.

## 9. Matriz de aceite e evidências mínimas

| ID | Critério obrigatório | Evidência produzida | Resultado requerido |
|---|---|---|---|
| AC-01 | Jupyter 01 executa do começo ao fim em kernel novo | `.executed.ipynb`, relatório de etapas | PASS |
| AC-02 | Leitura SQL/snapshot e hash reproduzíveis | SQL, contagem e hashes | PASS |
| AC-03 | Treino real e registro MLflow | experiment/run/metrics/model/version | PASS |
| AC-04 | Binário recuperado do RustFS e igual ao MLflow | SHA-256, URI e load/predict | PASS |
| AC-05 | Proposta DRAFT persistida e idempotente | SQL independente e rollback negativo | PASS |
| AC-06 | API retorna linhas idênticas ao banco | contagem, IDs e valores | PASS |
| AC-07 | IDs/lineage navegáveis partindo de proposta, run, modelo ou snapshot | `lineage-*.json`, SQL e API | PASS |
| AC-08 | Notebook 02 consome **endpoint HTTP** da API e mostra payload completo | notebook executado + JSON Schema | PASS |
| AC-09 | Notebook 02 valida regras e sinaliza `NOT_EVALUATED` quando faltam dados | tabela `rule_id` × status × motivo | PASS |
| AC-10 | Contrato API preserva retrocompatibilidade | contract tests + Swagger | PASS |
| AC-11 | Nenhum token/dado sensível nos artefatos | varredura sanitizada + teste negativo | PASS |
| AC-12 | Relação N:N de propostas e modelos sem perda de origem | teste com 2+ modelos/versões | PASS |
| AC-13 | Reinício/rebuild preserva run, binário, tags e proposta | reconciliação pós-restart | PASS |
| AC-14 | CI `development` passa em ambiente limpo ou bloqueio é reportado com causa provada | URL run e logs sanitizados | PASS (não dispensável) |
| AC-15 | Inventário de 30 e 500 modelos com métricas operacionais | catálogo e benchmark distinto de inferência | Medir e reportar; sem alegar PASS sem executar |
| AC-16 | Notebooks 00–09 disponíveis, documentados e sem sobrescrever workspace | catálogo, verificação de integridade e smoke de notebooks implementados | PASS ou NOT_IMPLEMENTED justificado |
| AC-17 | Notebook 09 `preview` lista todos os alvos e não modifica dados | manifesto do plano e comparação antes/depois | PASS |
| AC-18 | Reset destrutivo é recusado fora da POC, sem frase forte ou com escopo alterado | testes negativos automatizados | PASS |
| AC-19 | Factory-reset em stack descartável recria um ambiente sem modelos, runs, propostas e objetos antigos | relatório sanitizado e SQL/API/RustFS/MLflow pós-reset | PASS em ambiente descartável; **nunca executar no ambiente do usuário sem autorização** |
| AC-20 | Reset e rebootstrap preservam `.env`, notebooks editados e backups externos | hash/checklist de itens preservados | PASS |

**Cada teste deve informar:** `test_id`, `timestamp_utc`, branch/commit, `environment`, `execution_id`, `run_id`, `model_name/version`, `snapshot_id`, `proposal_id`, status, link/URI de evidência, limitação e motivo em caso de falha ou não execução.

## 10. Critérios de conclusão para o Codex

A entrega somente está concluída quando:

1. O notebook central demonstra a jornada real de ponta a ponta e o novo notebook de inferência consome, mostra e valida **a representação JSON da API que a aplicação receberá**, com evidência em SQL e lineage.
2. É possível localizar intuitivamente **a mesma proposta e seus modelos** a partir de MLflow, RustFS, PostgreSQL, API e relatório, sem depender de busca manual por timestamps.
3. A estrutura MLflow/Workbench para dezenas ou centenas de modelos está explicada e os vínculos N:N estão suportados, sem lançar 500 Jupyters/serviços.
4. README, catálogo de notebooks 00–09 e `/docs` permitem instalar, operar, validar, diagnosticar e reinicializar com segurança a POC sem adivinhações.
5. Notebook 09 tem inventário, pré-visualização, confirmação forte, controlador externo, reset de todos os dados exclusivos da POC, rebootstrap e testes negativos; **sem execução destrutiva no ambiente atual sem ordem humana explícita**.
6. Testes efetivamente executados e CI reportados com honestidade; nenhuma mudança operacional no GCP.

**Formato de retorno obrigatório do Codex:** resumo por fase, arquivos criados/alterados, migrações, contratos, notebooks, comandos exatos executados, tabela de testes PASS/FAIL/NOT_EXECUTED, evidências com paths reais, lacunas e próximos passos. Não tratar o DEMO como validação das 237 regras funcionais da V4.4.
