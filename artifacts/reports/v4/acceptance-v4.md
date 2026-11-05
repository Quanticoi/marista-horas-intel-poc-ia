# Aceite técnico V4 — 05/11/2026

**Estado: pronto para revisão local.** Fluxo real executado em Docker Compose; não é homologação acadêmica.

Código testado: `7335a5fe0a555bf6e9c57cff2e9732f9e9a576bd`. Fonte: estrutura de referência + histórico sintético, seed 42.

## Execução comprovada

- 11 serviços saudáveis e 19 verificações de acesso aprovadas.
- 12 notebooks executados em kernels novos, inclusive as cópias editáveis do workspace.
- Suíte principal: 136 aprovados e 1 pulado por exigir Jupyter. Suíte Workbench: 4 aprovados, incluindo esse caso (há sobreposição).
- Export Git limpo do código testado: 136 aprovados e 1 pulado. Usou os serviços existentes; não é instalação vazia nem CI remota.
- Mesma proposta, versões e trace disponíveis após rebuild; inferência reiniciada com Jupyter parado recuperou 1 PRELOAD e 2 LAZY.

Proposta: `41f15eac-1dc7-44e0-b360-db0e50da8406` — 70 ofertas, 107 atividades de origem.
Campanha: `cce085b3-fc01-4395-baaa-147e63046609`. Trace: `tr-d6ee4ffdbe17b5b8fe7d2437811c49f7`.

Modelos finais: `hi.demo.v4.c2248.components/8`, `hi.demo.v4.c2348.components/5`, `hi.demo.v4.c2287.components/5`.

## Matriz de aceite

| Critério | Automático | Evidência | Limite |
|---|---|---|---|
| V4-01 — 107 linhas com proveniência | AUTO_PASS | [academic-import-junit.xml](academic-import-junit.xml) | — |
| V4-02 — Cursos e turnos distintos | AUTO_PASS | [academic-import-junit.xml](academic-import-junit.xml) | — |
| V4-03 — P164: uma oferta, três atividades | AUTO_PASS | [application-view-final.json](application-view-final.json) | — |
| V4-04 — P110A e duplicidades preservadas | AUTO_PASS | [import-report.json](import-report.json) | 13 linhas em quarentena; não descartadas. |
| V4-05 — Contrato de entidades classificado | AUTO_PASS | [source-mapping.csv](source-mapping.csv) | Arquivo fornecido contém 31 entidades e 175 campos; diferença de 30 entidades da especificação documentada. |
| V4-06 — Simulação determinística | AUTO_PASS | [scenario-manifest.json](scenario-manifest.json) | Histórico sintético, seed 42. |
| V4-07 — Planejamento, matrícula e previsão separados | AUTO_PASS | [application-view-final.json](application-view-final.json) | — |
| V4-08 — Regulares por coorte e adicionais por disciplina | AUTO_PASS | [components-junit.xml](components-junit.xml) | Demonstração sintética; não matrícula oficial. |
| V4-09 — Pendências de modulação/unificação auditáveis | AUTO_PASS | [application-view-final.json](application-view-final.json) | S03 PENDING_DATA/PENDING_APPROVAL; regras institucionais não homologadas. |
| V4-10 — Cold start sem feedback inventado | AUTO_PASS | [scenario-manifest.json](scenario-manifest.json) | Feedback acadêmico ainda ausente. |
| V4-11 — Fit exclusivo no Workbench | AUTO_PASS | [worker-during-training.json](worker-during-training.json) | Bloqueio de treinamento operacional também coberto por serving-junit.xml. |
| V4-12 — Lotes, checkpoint, repetição e indicadores | NOT_EXECUTED | [application-notebook-proof.json](application-notebook-proof.json) | Repetição idempotente executada; interrupção forçada durante fit/retry após falha não executada nesta V4. UX visual não conferida. |
| V4-13 — Métricas selecionáveis e aplicabilidade | AUTO_PASS | [full-suite-junit.xml](full-suite-junit.xml) | — |
| V4-14 — Métricas por modelo/lote/campanha | AUTO_PASS | [mlflow-campaign-summary.json](mlflow-campaign-summary.json) | Métricas sintéticas não comprovam qualidade institucional. |
| V4-15 — Identidade e hashes entre serviços | AUTO_PASS | [final-lineage.json](final-lineage.json) | — |
| V4-16 — Governança e catálogo de serving | AUTO_PASS | [serving-catalog-final.json](serving-catalog-final.json) | Aprovação técnica DEMO, não homologação acadêmica. |
| V4-17 — Inferência sem Jupyter | AUTO_PASS | [jupyter-during-restart-final.json](jupyter-during-restart-final.json) | — |
| V4-18 — Restart e revogação de cache | AUTO_PASS | [restart-inference-final.json](restart-inference-final.json) | Revogação/reaprovação controladas: serving-junit.xml. |
| V4-19 — Contrato HTTP v2, filtros e schema | AUTO_PASS | [full-suite-junit.xml](full-suite-junit.xml) | — |
| V4-20 — Notebook 09 exclusivamente HTTP | AUTO_PASS | [notebooks/09_simulador_aplicacao.executed.ipynb](notebooks/09_simulador_aplicacao.executed.ipynb) | Execução automática; interação visual do usuário não conferida. |
| V4-21 — S01/S02 e S03 pendente | AUTO_PASS | [application-view-final.json](application-view-final.json) | — |
| V4-22 — Auditoria completa do resultado | AUTO_PASS | [final-lineage.json](final-lineage.json) | VERIFIED técnico, não aprovação de negócio. |
| V4-23 — Preservação no rebuild e migrations aditivas | AUTO_PASS | [final-proof.json](final-proof.json) | Mesma proposta, versões e trace após rebuild; nenhum reset principal. Não é comparação byte a byte de todo o banco legado. |
| V4-24 — CI limpa e testes completos | NOT_EXECUTED | [clean-checkout-junit.xml](clean-checkout-junit.xml) | Export Git 7335a5f sem dev/history passou localmente usando serviços existentes e referências externas. CI remota e instalação vazia não executadas. |
| V4-25 — Evidências e limites explícitos | AUTO_PASS | [acceptance-v4.json](acceptance-v4.json) | Todos os checks visuais: MANUAL_NOT_CHECKED. |

V4-12 fica NOT_EXECUTED no aceite integral: lote e repetição passaram, mas não houve falha forçada no meio do fit. V4-24 fica NOT_EXECUTED para CI remota. Nenhum desses estados significa que o código não foi implementado.

Todas as verificações visuais permanecem **MANUAL_NOT_CHECKED**. O diagnóstico Markdown complementar não foi fornecido. S03 representa uma pendência real, sem capacidade ou unificação inventadas.

## Reproduzir e consultar

Siga o [runbook V4](../../../docs/operations/POC_V4_MANUAL_RUNBOOK.md). Para apenas subir o ambiente: `./deployment/scripts/compose.ps1 start`.
Abra [Jupyter](http://localhost:8888/lab/tree/notebooks/00_ambiente.ipynb), [MLflow](http://localhost:5000), [RustFS](http://localhost:9001) e [API](http://localhost:8000/docs). Credenciais permanecem no `.env` local.

Dados acadêmicos/propostas: `planejamento_db.planning`. Tracking/Registry: `mlflow_db`, administrado pelo MLflow. Binários e manifests: bucket `pucpr-poc` no RustFS.

Revalidar a mesma proposta sem treinar: `docker compose run --rm --no-deps --entrypoint python tools -m tests.acceptance.v4_evidence`.

## Integridade das evidências

Relatórios iniciais conservam seus próprios IDs e versões. A rodada final está em `*-final.json`, `final-proof.json`, `application-notebook-proof.json` e notebooks executados. Não somar ensaios sobrepostos como testes independentes.
O índice [evidence-sha256.json](evidence-sha256.json) registra os bytes das evidências desta entrega. A matriz JSON inclui código, fonte, data, configuração e hashes do contrato.
