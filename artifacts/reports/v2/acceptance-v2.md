# Aceite V2 e revisão do repositório

PASS — 2026-11-04T20:16:52.218627+00:00

Código da última conferência local: 798b586ce95ae163251a025efafeac4e2fe21863. Relatório: 798b586ce95ae163251a025efafeac4e2fe21863. Testes finais: 79.

| Critério | Cenário | Resultado | Evidência |
|---|---|---|---|
| V2-01 | Jornada01 em kernel novo | PASS | [journey-latest.json](../journey-latest.json), [01_jornada_completa_planilha_turmas.executed.ipynb](../01_jornada_completa_planilha_turmas.executed.ipynb) |
| V2-02 | API gera DRAFT e reconcilia SQL/S3 | PASS | [probe-complete.json](../v2/probe-complete.json) |
| V2-03 | Idempotência, conflito e recuperação | PASS | [final-junit.xml](../v2/final-junit.xml), [worker-restart-recovered.json](../v2/isolated/worker-restart-recovered.json) |
| V2-04 | Notebook02: leitura e geração HTTP | PASS | [notebook-suite.json](../v2/isolated/notebook-suite.json) |
| V2-05 | Contrato técnico e limites V4.4 | PASS | [final-junit.xml](../v2/final-junit.xml), [probe-complete.json](../v2/probe-complete.json) |
| V2-06 | Registry e hashes no Object Store | PASS | [journey-latest.json](../journey-latest.json) |
| V2-07 | Linhagem N:N e busca reversa | PASS | [lineage-cross-system.json](../v2/lineage-cross-system.json), [lineage-negative-tests.json](../v2/lineage-negative-tests.json) |
| V2-08 | Campanhas persistentes e controles | PASS | [campaign-controls.json](../v2/isolated/campaign-controls.json), [worker-restart-recovered.json](../v2/isolated/worker-restart-recovered.json) |
| V2-09 | 30 treinamentos reais | PASS | [training-campaign-30.json](../v2/training-campaign-30.json) |
| V2-10 | 500 treinamentos reais | PASS | [training-campaign-500.json](../v2/training-campaign-500.json) |
| V2-11 | Aprovação/revogação/rollback isolados | PASS | [lineage-negative-tests.json](../v2/lineage-negative-tests.json) |
| V2-12 | Dois resets e jornadas pós-rebuild isolados | PASS | [reset-isolated-proof.json](../v2/reset-isolated-proof.json), [reset-independent-empty.json](../v2/isolated/reset-independent-empty.json), [reset-independent-demo-ready.json](../v2/isolated/reset-independent-demo-ready.json) |
| V2-13 | Dados e arquivos anteriores preservados | PASS | [preservation-after.json](../v2/preservation-after.json) |
| V2-14 | Dez notebooks; opt-ins e edição após restart | PASS | [catalog-smoke.json](../catalog-smoke.json), [notebook-suite.json](../v2/isolated/notebook-suite.json), [jupyter-editability.json](../v2/jupyter-editability.json) |
| V2-15 | CI remoto em checkout limpo | PASS | [ci-result.json](../v2/ci-result.json) |
| V2-16 | README, arquitetura, comandos e índices | PASS | [README.md](../../../README.md) |

## Demonstração local

Jornada01: modelo v15, run `c0d9f3138c874049b339e0f54ab8348c`, proposta `712b11cd-a96a-4bb9-83bb-691724ceae88`.
Geração pela API: `6391c652-a079-4a73-a6c6-a385e8b9774f`. Cada proposta contém 90 linhas DEMO.

[Jupyter](http://localhost:8888) · [MLflow](http://localhost:5000) · [RustFS](http://localhost:9001) · [API](http://localhost:8000/docs) · [Logs](http://localhost:8088)

Banco mlflow_db: tracking/Registry; planejamento_db.planning: snapshots, propostas e operações; RustFS/pucpr-poc: modelos e manifests.

Windows: `deployment/scripts/compose.ps1 start`. Abra `01_jornada_completa_planilha_turmas.ipynb` e use Restart Kernel and Run All. Jornada operacional: notebook02, modo GENERATE_AND_VALIDATE com confirmação explícita.

## Limitações

- Dados sintéticos e regra provisória; não homologa o contrato acadêmico V4.4
- 500 identidades experimentais treinadas no mesmo snapshot DEMO; não são 500 séries acadêmicas reais nem 500 modelos simultâneos em memória
- Resets/falhas destrutivas executados somente na stack isolada; volumes principais preservados
- Evidências mantêm seu commit/hash original; cada ensaio identifica a versão executada; CI identifica seu próprio HEAD
- Warnings de depreciação de dependências não impediram os testes
