# Roteiro V4 — execução local

Jornada implementada: importação SQL → simulação → treinamento no Workbench →
revisão técnica → deploy → inferência → proposta persistida → tabela HTTP → auditoria.
O relatório em artifacts/reports/v4/application-notebook-proof.json registra kernels
novos. MANUAL_NOT_CHECKED significa que não foi presumida inspeção visual pelo usuário.

## Preparação

Docker Desktop Linux, Python3.11/3.12 administrativo e8GiB iniciais para Docker.
Jupyter: limite3GiB, concorrência1..2. Não é ensaio de500 modelos residentes.
Coloque as três planilhas em data/reference; /reference é somente leitura no container.
As107 linhas são planejamento, não matrícula realizada. Os quatro PDFs foram
conferidos em [V4_SOURCE_REVIEW](../architecture/V4_SOURCE_REVIEW.md); o diagnóstico
Markdown complementar ainda não foi fornecido. Isso não bloqueia o cenário demonstrativo.

PowerShell, na raiz:

```powershell
.\deployment\scripts\compose.ps1 init
# Instalação existente:
.\deployment\scripts\compose.ps1 rebuild
.\deployment\scripts\compose.ps1 start
```

Linux: `sh deployment/scripts/journey.sh rebuild`. Serviços usam DNS Compose;
o navegador usa localhost. Credenciais somente no .env. Rebuild não limpa volumes,
não treina, não aprova e não substitui edições sem preservar a cópia anterior.

## Jupyter

Abra http://localhost:8888/lab/tree/notebooks/00_ambiente.ipynb.
Execute00–03: dependências, importação idempotente, qualidade e snapshot seed42.
04 treina uma identidade;05 treina os três cursos. Os checkboxes de métricas afetam
a execução da próxima célula. Mesma chave/configuração recupera a campanha;
para mudar algoritmo/métricas/snapshot, use outra chave intencionalmente.

06 mostra MAE/RMSE e demais métricas habilitadas, com baseline e agregação por
target/split/horizonte. Regular é avaliado por coorte/ciclo; adicionais por oferta/ciclo.
Métricas de dados sintéticos não atestam qualidade institucional.

07: confira nome, versão, run, SHA e motivo; defina APPROVE_DEMO=True.
08: defina DEPLOY_DEMO=True e GENERATE=True após a decisão. PRELOAD é seletivo,
LAZY não ocupa memória antes da primeira chamada. A proposta completa usa os três
cursos do05. Contexto salvo em workspace/reports/v4-context.json leva os IDs ao09.
09 pagina, confere schema/hash e mostra filtros HTTP; abra2248/P164 e2287/período2.
10 confronta PostgreSQL/Registry/RustFS.11 apenas orienta o controlador excepcional.

## Conferência externa

- MLflow: http://localhost:5000, experimento HI/POC/PlanilhaTurmas/academic-components/2024-2.
  Runs pai/lote/modelo, métricas, CSVs de erros e Registry por nome/versão.
- RustFS: http://localhost:9001, bucket pucpr-poc. Binário no prefixo MLflow;
  índices em lineage/poc/planilha-turmas/v4/models e manifests de propostas/inferências.
- PostgreSQL: planejamento_db.planning, workbench_models, academic_deployments,
  ai_proposals_v2 e ai_proposal_offers_v2. Metadados MLflow ficam em mlflow_db.
- API: http://localhost:8000/docs, GET /v2/proposals/{id}/application-view e
  GET /v2/audit/proposals/{id}, autenticados. Nenhum novo treino para consulta.
- Dashboard: http://localhost:8088, eventos por correlation_id/job_id/run_id.

ConsultaSQL sem credenciais embutidas:

```sql
SELECT proposal_id,cycle_code,revision,status,payload_sha256,manifest_uri
FROM planning.ai_proposals_v2 ORDER BY generated_at DESC;
SELECT proposal_id,count(*) AS ofertas FROM planning.ai_proposal_offers_v2 GROUP BY proposal_id;
SELECT model_key,state,run_id,result->>'model_version' AS version FROM planning.workbench_models;
```

## Testes e limites

```powershell
docker compose run --rm --no-deps -v "${PWD}:/app:ro" -v "${PWD}/data/reference:/reference:ro" --entrypoint python tools -m pytest tests/unit tests/integration -q -o cache_dir=/tmp/pytest --junitxml=/reports/v4/full-suite-junit.xml
docker compose run --rm --no-deps -v "${PWD}:/app:ro" --entrypoint /usr/local/bin/_entrypoint.sh jupyter python -m pytest tests/integration/test_workbench_v4.py -q -o cache_dir=/tmp/pytest
```

Ensaio de todos os notebooks com aprovação técnica DEMO explícita:
`docker compose run --rm --no-deps --entrypoint /usr/local/bin/_entrypoint.sh jupyter python -m src.workbench.v4_notebook_suite --approve-demo`.
Esse comando treina/aprova/publica as versões DEMO selecionadas; não é bootstrap.
Linux usa os mesmos comandos, com $PWD. Bash não foi executado nesta estação Windows.

Provas: worker parado durante treino; checksums RustFS/proxy; mesma chave sem duplicação;
revogação com cache quente; Jupyter parado durante restart; PRELOAD/LAZY recuperados.
Não alegar nova prova de reset destrutivo V4, homologação acadêmica ou CI remota sem
evidência específica. Quarentena, falta de capacidade e unificação pendente são resultados
do contrato, não campos a preencher artificialmente. Nenhuma revisão humana é sobrescrita.
