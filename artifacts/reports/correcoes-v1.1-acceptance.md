# Correções v1.1 — relatório de execução

UTC: 2026-11-04T15:26:29.289950+00:00. Branch development. Código validado no CI: `feebce942e982bde2723ae82f1ef220f2c269438`.

## Entrega por fase

| Fase | Implementação e evidência |
|---|---|
| A | Inventário, V3/V4.4 consultados e matriz: correcoes-fase-a-2026-11-04.md |
| B | src/common/lineage.py: identidade tipada, hashes canônicos e manifests condicionais |
| C | Migration005: grafo, N:N, evidência de contrato, vista/índices/backfill parcial |
| D | Tags MLflow/Registry, inference_id, traces, atribuição por linha e manifests S3 |
| E | Pydantic/JSON Schema poc-planilha-turmas-v1, application-view e lookup autenticados |
| F | Notebooks00–09, distribuição sem clobber, controlador externo de reset e wrappers |
| G |30treinos reais e500identidades medidos; scheduler persistente permanece pendente |
| H | README, LINEAGE, contrato, cobertura funcional, operação/reset e ADR009 |
| I |59testes locais/CI,19checksHTTP,notebooks,preservação e resetsisolados |

## Resultado principal

Proposta `8d373b5a-f73d-4daa-b5cb-cde6ac238087`; run `6d3153d23589442b8475e969f82a1d98`; experimento4; modelo `planilha-turmas-demo` v11.
1050 registros SQL →90linhas DRAFT/API. MAE 3.758631; RMSE 4.914227. Métricas DEMO.
[Run MLflow](http://127.0.0.1:5000/#/experiments/4/runs/6d3153d23589442b8475e969f82a1d98) · [CI aprovado](https://github.com/Quanticoi/marista-horas-intel-poc-ia/actions/runs/41847743558).

## Matriz de aceite

| Teste | Estado | Evidência / limite |
|---|---|---|
| AC-01 | PASS | [01_jornada_completa_planilha_turmas.executed.ipynb](01_jornada_completa_planilha_turmas.executed.ipynb) — Kernel novo, jornada integral |
| AC-02 | PASS | [journey-latest.json](journey-latest.json) — 1050 linhas SQL, hashes distintos de snapshot/extração |
| AC-03 | PASS | [journey-latest.json](journey-latest.json) — fit/predict reais, MAE/RMSE, Registry |
| AC-04 | PASS | [journey-latest.json](journey-latest.json) — Três arquivos comparados byte a byte via SHA256 |
| AC-05 | PASS | [compose-junit.xml](compose-junit.xml) — Idempotência, conflito e rollback testados |
| AC-06 | PASS | [journey-latest.json](journey-latest.json) — 90 linhas reconciliadas SQL/API |
| AC-07 | PASS | [compose-junit.xml](compose-junit.xml) — Lookup reverso por proposta/run/modelo/snapshot |
| AC-08 | PASS | [02_teste_inferencia_planilha_turmas.executed.ipynb](02_teste_inferencia_planilha_turmas.executed.ipynb) — HTTP real, páginas e schema |
| AC-09 | PASS | [inference-contract-8d373b5a-f73d-4daa-b5cb-cde6ac238087.json](inference-contract-8d373b5a-f73d-4daa-b5cb-cde6ac238087.json) — Regras não demonstradas marcadas NOT_EVALUATED |
| AC-10 | PASS | [compose-junit.xml](compose-junit.xml) — Rotas antigas preservadas e contrato aditivo |
| AC-11 | PASS | [correcoes-unit-final.xml](correcoes-unit-final.xml) — Guardas de metadados; scan de segredos locais executado sem correspondências |
| AC-12 | PASS | [correcoes-isolated/multi-model-proposal.json](correcoes-isolated/multi-model-proposal.json) — Duas versões reais contribuíram para90 linhas; stack de teste depois resetada |
| AC-13 | PASS | [preservation-after-correcoes.json](preservation-after-correcoes.json) — Modelo v8, run e90linhas anteriores preservados após rebuild |
| AC-14 | PASS | [ci-correcoes.json](ci-correcoes.json) — CI Linux limpo passou,59testes,notebooks01/02 |
| AC-15 | PASS | [correcoes-isolated/model-benchmark.json](correcoes-isolated/model-benchmark.json) — 30treinos11.00s;500identidades0.34s;500treinos não executados |
| AC-16 | PASS | [catalog-smoke.json](catalog-smoke.json) — 00–09 disponíveis;04/07 opt-in não acionado; scheduler05 NOT_IMPLEMENTED |
| AC-17 | PASS | [reset-preview-proof.json](reset-preview-proof.json) — Hashes antes/depois idênticos; nenhum dado removido |
| AC-18 | PASS | [correcoes-unit-final.xml](correcoes-unit-final.xml) — Recusa ambiente/labels/escopo/semfrase/planomodificado/obsoleto |
| AC-19 | PASS | [correcoes-isolated/reset-independent-proof.json](correcoes-isolated/reset-independent-proof.json) — Factory-reset/demo-ready e reset-data/empty isolados; SDK/API/SQL/S3/filas conferidos |
| AC-20 | PASS | [workspace-after-correcoes.json](workspace-after-correcoes.json) — Original do usuário preservado; planos/resultados conferem hashes de.env/notebooks/backups |

PASS do catálogo05 significa consulta executável; não significa scheduler implementado.

## Operar e abrir os notebooks

```powershell
.\deployment\scripts\compose.ps1 start
.\deployment\scripts\compose.ps1 journey
.\deployment\scripts\compose.ps1 test
```
Jupyter http://localhost:8888; MLflow5000; API8000/docs; inferência8001/docs; RustFS9001; dashboard8088.
A cópia editada foi preservada (SHA256 AB37343F32483440DB03F8598617761E4A64A4EB24034FDBC50A4C3902614533).
Abra `01_jornada_completa_planilha_turmas.update-eeacc6e47d5c.ipynb` para a jornada atualizada e use Restart Kernel and Run All.
No02 informe explicitamente o proposal_id acima. Todos os notebooks foram confirmados writable=true pela API Jupyter.

## Persistência

planejamento_db/planning: dados sintéticos, propostas/linhas, auditoria, modelos operacionais e lineage. mlflow_db: metadados administrados pelo MLflow. RustFS/pucpr-poc: mlflow/, snapshots/, lineage/. Workspace é bind mount preservado.

## Diagnóstico CI e comandos efetivamente executados

1. Falha original reproduzida em volumes novos: `mlflow db upgrade` → UndefinedTable metrics. SDK MLflow inicializa o schema novo antes do upgrade; nenhuma migration própria do MLflow.
2. CI41846141084 passou provisioning e falhou ao gravar relatório644 do checkout. Permissão da pasta de relatórios corrigida; CI41847743558 passou integralmente.
```powershell
python dev/validate_static.py
python dev/generate_compose.py --check
python deployment/scripts/build_journey_notebook.py --check
docker compose build mlflow jupyter
docker compose run --rm --no-deps tools migrate
docker compose up -d --wait --wait-timeout 300
.\deployment\scripts\compose.ps1 journey
.\deployment\scripts\compose.ps1 test
docker compose exec -T jupyter /usr/local/bin/_entrypoint.sh python -m src.workbench.preservation_check
docker compose exec -T jupyter /usr/local/bin/_entrypoint.sh python -m src.workbench.smoke_catalog --proposal-id 93519267-7809-4e64-9e04-a79b9fb03d40 --reset-plan-id ef831e6f-361e-4e60-9fcc-8a740ee61a61
python dev/prove_preview.py
python dev/check_evidence_secrets.py
```
Ensaios isolados usaram `docker compose --env-file .env -f .runtime/correcoes-isolated/compose.json` com módulos execute_journey, benchmark e multi_model_proof. Relatórios preservados em correcoes-isolated/. Containers de teste foram parados; os da POC principal permanecem disponíveis.

Reset foi chamado exclusivamente com project=marista-correcoes-isolated, --execute, frase forte e planos8479badb-3529-4e07-b94f-88355fe8a25a(factory/demo-ready) e344098cc-fa0d-4241-b357-6aafc2e94d3e(data/empty). Veja planos/resultados em reset/. Não reproduza esses comandos no projeto principal.

## Limites e próximos incrementos

- Contrato provisório; não homologa237regras V4.4 nem integra fontes institucionais
- Scheduler persistente/retry/checkpoint de campanhas05 NOT_IMPLEMENTED; incremento permitido pela spec
- 500identidades não são500treinos/modelos registrados/APIs/modelos carregados
- Aprovação/publicação/revisão humana não exercitadas pelo catálogo de leitura
- Reset destrutivo somente na stack descartável; nenhum reset executado no projeto marista
- Revisão final do bootstrap PowerShell mantém PROPOSAL_ID vazio; sintaxe verificada localmente
