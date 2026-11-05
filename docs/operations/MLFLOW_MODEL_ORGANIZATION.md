# Organização de modelos e capacidade

| Nível | Organização V4 |
|---|---|
| Servidor MLflow | Um por ambiente da POC |
| Experimento | Um por nova campanha; ciclo + UTC + UUID |
| Runs | CAMPAIGN → BATCH → MODEL, com tags de campanha/lote/escopo |
| Modelo registrado | Identidade estável `hi.demo.v4.c{curso}.components` |
| Versão | Novo ajuste do modelo; ligada à run, dataset, código e hashes |
| Aprovação/deploy | Decisões explícitas, separadas do treino |

Essa organização permite comparar ensaios sem sobrescrever resultados. Para retomar,
informe a chave existente em RESUME. Para outra configuração, inicie NEW. O contexto
SQL fica em `workbench_campaigns/workbench_models`; treinamento não é enviado ao Celery.

## Crescer para centenas de modelos

O executor possui lotes e checkpoints, com concorrência limitada a 1–2 no Jupyter.
A capacidade de manter 500 identidades no Registry não equivale a executar 500 fits
ou manter 500 modelos em memória simultaneamente. O serving atual tem cache de
quatro versões por processo, PRELOAD seletivo e LAZY.

Antes de ampliar, medir duração/CPU/RSS por campanha, tamanho de artefato, latência,
memória de inferência e frequência de uso por identidade. A V4 executada comprova
três cursos. Os testes de 500 treinamentos V2 são históricos e não validam a V4.
Não há promessa de paralelismo ou dimensionamento institucional nesse número.

[Tags e identidade](../contracts/HI_TAGGING_STANDARD.md) · [Governança](REVIEW_INTEGRITY.md).
