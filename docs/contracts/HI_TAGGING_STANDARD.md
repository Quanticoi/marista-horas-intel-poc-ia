# HI-LINEAGE/1.1 — nomes e índices de auditoria

Extensão aditiva de [HI-LINEAGE/1.0](../architecture/LINEAGE.md). Não reescreve
manifests, runs, aliases nem PKs anteriores. Modelo de identidade: solução → ambiente
→ domínio → ciclo → snapshot → família/escopo → campanha → run → versão → inferência → proposta.

Nas tabelas abaixo, destino **R/V/C/M** significa run, Model Version, catálogo SQL
e manifest imutável. Campos de inferência/proposta ficam nas tabelas e manifests
existentes, nunca são inventados para um treino. Cardinalidade 1 por versão,
exceto campanhas 1:N jobs e proposta N:N modelos/inferências. Tags são strings;
JSON preserva tipos. Nulos legítimos são omitidos nas tags. Campos de escopo são
obrigatórios para hi.pt.demanda; não aplicáveis aos ensaios agregados hi.demo.
O schema 1.0 permanece aceito; ausência de comprovação retorna LEGACY_PARTIAL.

| Campo | Tipo | Significado | Origem | Destino | Obrigatoriedade/cardinalidade | Exemplo | Compatibilidade |
|---|---|---|---|---|---|---|---|
| solution_id | string | Solução | constante | R/V/C/M | 1 quando aplicável | horarios-inteligentes | aditivo; legado ausente não inferido |
| environment | enum | Ambiente | configuração | R/V/C/M | 1 quando aplicável | poc | aditivo; legado ausente não inferido |
| domain | enum | Domínio | constante | R/V/C/M | 1 quando aplicável | planilha-turmas | aditivo; legado ausente não inferido |
| source_type | enum | Origem declarada | snapshot | R/V/C/M | 1 quando aplicável | DEMO | aditivo; legado ausente não inferido |
| cycle_code | string | Semestre alvo | academic_cycles | R/V/C/M | 1 quando aplicável | 2026-1 | aditivo; legado ausente não inferido |
| academic_cycle_id | UUID | PK ciclo | academic_cycles | R/V/C/M | 1 quando aplicável | UUID SQL | aditivo; legado ausente não inferido |
| campus_code | string | Código sintético campus | campuses | R/V/C/M | 1 quando aplicável | DEMO-C1 | aditivo; legado ausente não inferido |
| course_code | string | Código sintético curso | courses | R/V/C/M | 1 quando aplicável | DEMO-CR1 | aditivo; legado ausente não inferido |
| period_code | string | Período cadastrado | academic_periods | R/V/C/M | 1 quando aplicável | P1 | aditivo; legado ausente não inferido |
| model_family | string | Família preditiva | configuração | R/V/C/M | 1 quando aplicável | demanda-alunos | aditivo; legado ausente não inferido |
| snapshot_id | UUID | Fotografia selada | dataset_snapshots | R/V/C/M | 1 quando aplicável | UUID SQL | aditivo; legado ausente não inferido |
| snapshot_sha256 | SHA256 | Hash manifest original | snapshot SQL | R/V/C/M | 1 quando aplicável | 64 hex | aditivo; legado ausente não inferido |
| dataset_sha256 | SHA256 | CSV efetivamente usado no escopo | extração SQL filtrada | R/V/C/M | 1 quando aplicável | 64 hex | aditivo; legado ausente não inferido |
| dataset_schema_version | string | Schema da fonte | dataset_snapshots | R/V/C/M | 1 quando aplicável | 1.0 | aditivo; legado ausente não inferido |
| data_as_of_utc | UTC ISO8601 | Data de corte (meia-noite UTC da data original) | dataset_snapshots | R/V/C/M | 1 quando aplicável | 2025-12-31T00:00:00+00:00 | aditivo; legado ausente não inferido |
| query_version | string | Consulta versionada | journey_history.sql | R/V/C/M | 1 quando aplicável | journey-history-v1 | aditivo; legado ausente não inferido |
| training_campaign_id | UUID nullable | Campanha persistente | training_campaigns | R/V/C/M | 1 quando aplicável | UUID SQL | aditivo; legado ausente não inferido |
| campaign_display_name | string até160 | Rótulo não identificador | request validado | R/V/C/M | 1 quando aplicável | POC DEMO • Validação manual | aditivo; legado ausente não inferido |
| operation_job_id | UUID nullable | Job persistente | operation_jobs | R/V/C/M | 1 quando aplicável | UUID SQL | aditivo; legado ausente não inferido |
| training_execution_id | UUID | Execução de treino (job) | operation_jobs | R/V/C/M | 1 quando aplicável | UUID SQL | aditivo; legado ausente não inferido |
| experiment_id | native string | Experimento MLflow | SDK | R/V/C/M | 1 quando aplicável | 4 | aditivo; legado ausente não inferido |
| experiment_name | string | Agrupador domínio/ciclo | convenção fixa | R/V/C/M | 1 quando aplicável | HI/POC/PlanilhaTurmas/Demanda/2026-1 | aditivo; legado ausente não inferido |
| run_id | native hex32 | Tentativa MLflow | SDK | R/V/C/M | 1 quando aplicável | ID nativo | aditivo; legado ausente não inferido |
| run_name | string | Tentativa legível UTC+algoritmo | contexto+clock+attempt | R/V/C/M | 1 quando aplicável | DEMO escopo__ridge__UTC__a01__jobcurto | aditivo; legado ausente não inferido |
| algorithm | enum | Estimador ajustado | request | R/V/C/M | 1 quando aplicável | ridge | aditivo; legado ausente não inferido |
| code_version | SHA256 | Conteúdo fontes/config | source_version | R/V/C/M | 1 quando aplicável | 64 hex | aditivo; legado ausente não inferido |
| config_hash | SHA256 | Parâmetros canônicos | treino | R/V/C/M | 1 quando aplicável | 64 hex | aditivo; legado ausente não inferido |
| feature_schema_hash | SHA256 | Nomes e tipos features | DataFrame de treino | R/V/C/M | 1 quando aplicável | 64 hex | aditivo; legado ausente não inferido |
| model_key | string até160 | Identidade funcional estável | PKs/códigos catálogo | R/V/C/M | 1 quando aplicável | hi.pt.demanda.DEMO-C1.DEMO-CR1.P1 | aditivo; legado ausente não inferido |
| model_display_name | string | Rótulo histórico DEMO | contexto SQL no treino | R/V/C/M | 1 quando aplicável | Planilha Turmas DEMO • DEMO-C1 • DEMO-CR1 • Período 1 | aditivo; legado ausente não inferido |
| registered_model_name | string | Nome Registry | SDK | R/V/C/M | 1 quando aplicável | igual model_key | aditivo; legado ausente não inferido |
| model_version | inteiro positivo | Versão nativa, tags string | SDK | R/V/C/M | 1 quando aplicável | 3 | aditivo; legado ausente não inferido |
| artifact_uri | URI | Referência lógica (não chave S3) | SDK | R/V/C/M | 1 quando aplicável | models:/m-… | aditivo; legado ausente não inferido |
| artifact_sha256 | SHA256 | Bytes model.pkl | download proxy | R/V/C/M | 1 quando aplicável | 64 hex | aditivo; legado ausente não inferido |
| model_signature_hash | SHA256 | Assinatura inputs/outputs canônica | MLflow ModelSignature | R/V/C/M | 1 quando aplicável | 64 hex | aditivo; legado ausente não inferido |
| validation_status | enum | Candidato técnico, NÃO aprovação | registro | R/V/C/M | 1 quando aplicável | DEMO_CANDIDATE | aditivo; legado ausente não inferido |
| inference_id | UUID nullable | Invocação efetiva | serviço inferência | SQL/manifest/trace aplicável | quando aplicável; N:N por contribuição | UUID nativo | aditivo; legado ausente não inferido |
| proposal_id | UUID nullable | Geração de negócio | worker | SQL/manifest/trace aplicável | quando aplicável; N:N por contribuição | UUID job geração | aditivo; legado ausente não inferido |
| proposal_revision | inteiro positivo | Revisão negócio independente da versão | contrato | SQL/manifest/trace aplicável | quando aplicável; N:N por contribuição | 1 | aditivo; legado ausente não inferido |
| proposal_schema_version | string | Contrato provisório | contrato API | SQL/manifest/trace aplicável | quando aplicável; N:N por contribuição | poc-planilha-turmas-v1 | aditivo; legado ausente não inferido |
| ruleset_version | string | Regra provisória | persistence.journey | R/V/C/M | 1 quando aplicável | ceil-capacity-v1 | aditivo; legado ausente não inferido |
| ruleset_hash | SHA256 | Regra+capacidade canônicos | composição | R/V/C/M | 1 quando aplicável | 64 hex | aditivo; legado ausente não inferido |
| correlation_id | string até120 | Correlação transversal | HTTP/notebook | R/V/C/M | 1 quando aplicável | UUID | aditivo; legado ausente não inferido |
| trace_id | native nullable | Trace real, sem payloads | MLflow tracing | SQL/manifest/trace aplicável | quando aplicável; N:N por contribuição | tr-… | aditivo; legado ausente não inferido |

Nomes: Unicode NFKC e maiúsculas nos códigos, apenas ASCII A–Z/0–9/hífen,
até 40 caracteres por componente e 160 por chave. Não transliterar nomes:
código incompatível falha. A consulta verifica colisões contra catalog_id antes
de treinar; nomes pessoais não entram em keys. Renomear display não altera PK.
DEMO-C1/DEMO-CR1 são rótulos dos códigos sintéticos C1/CR1 existentes, sem afirmar
cadastro institucional. Período vem do SQL. Legados planilha-turmas-demo,
C1-CR1-P1 e hi.demo.* mantêm seus caminhos próprios.

Experimento por ciclo; não por versão nem por modelo. Run inclui UTC, algoritmo,
tentativa e job curto. campaign_display_name é editado na submissão; não é PK.
Novos treinos por escopo filtram period_id **antes** do split temporal e hash CSV.
Comparação exige mesmo snapshot, escopo, dataset, alvo e janela.

Campos partilhados são conferidos antes do serving (inclusive cache quente).
Registro exige run FINISHED e assinatura; catálogo só é publicado após comparar
bytes proxy/S3 e assinatura. V1 não ganha VERIFIED por existir no Registry.
RECORDED em view significa evidência registrada; VERIFIED vem da reconciliação viva.

Autorização corrente: planning.model_approval_requests + alias champion concordante.
validation_status e status_at_creation não autorizam uso operacional.
Manifests têm data original da versão, arquivos com chave real/bytes/SHA e SQLref;
escrita condicional IfNoneMatch, mesmo conteúdo idempotente, colisão rejeitada.
Não gravar aprovação mutável no manifest nem copiar model.pkl para catálogo.
