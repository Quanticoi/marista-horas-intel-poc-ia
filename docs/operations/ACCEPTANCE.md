# Aceite V4

Há três níveis distintos: implementação, execução automática e conferência humana.
Use a [matriz V4-01…25](../../artifacts/reports/v4/acceptance-v4.md) para a rodada
principal e o [relatório dos ajustes](../../artifacts/reports/v4-adjustments/README.md)
para experimento por campanha, reset seletivo e revisão documental.

O ensaio principal executou os 12 notebooks em kernels novos, treinamento real,
reload dos artefatos, proposta SQL/API, idempotência, revogação com cache aquecido,
restart sem Jupyter e preservação após rebuild. Isso não homologa qualidade acadêmica.

## Conferência manual ainda necessária

| Interface | O que observar |
|---|---|
| Jupyter 01–03 | Origem, quarentena, P164 e legenda de dados sintéticos |
| Jupyter 04/05 e MLflow | Novo experimento, runs filhas, métricas e links |
| Registry / RustFS | Mesma versão, run, manifesto e hash de artefato |
| Jupyter 07/08 | Decisão técnica explícita; diferença entre deploy e modelo carregado |
| Jupyter 09 | Filtros HTTP e atividades filhas da oferta |
| Jupyter 10 | Auditoria técnica, pendências funcionais preservadas |

Estado visual: **MANUAL_NOT_CHECKED** até observação real. CI remota exige execução
identificada e acesso ao pacote de referências, que não é publicado no Git.
As provas de CI V2/V3 não substituem CI V4.
