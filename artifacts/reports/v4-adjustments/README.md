# Ajustes V4 — campanhas, reset seletivo e documentação

Solicitação posterior à rodada de aceite principal de 05/11/2026.

- Cada campanha NEW cria experimento próprio; RESUME exige chave existente.
- Reset seletivo limpa MLflow e objetos/resultados derivados, mantendo cinco tabelas de origem SQL.
- README e documentação operacional revisados para V4; manuais V2/V3 explicitamente históricos.

## Executado

| Prova | Evidência |
|---|---|
| Duas campanhas e dois experimentos reais, com IDs distintos | [campaign-policy.json](campaign-policy.json) |
| Retomada sem duplicar e chave inexistente rejeitada | [campaign-policy.json](campaign-policy.json) |
| MLflow e versões de objetos removidos; origem com contagens/hashes idênticos | [selective-reset.json](selective-reset.json) |
| Treinamento posterior usa a mesma origem, sem reimportar | [post-reset-training.json](post-reset-training.json) |
| Regressão: 139 aprovados, 1 pulado por exigir Jupyter | [suite-junit.xml](suite-junit.xml) |

Reset real executado exclusivamente em `marista-correcoes-isolated`. A comprovação
de vazio é anterior ao treinamento posterior intencional, que cria novos artefatos.
Os IDs desse ensaio pertencem à stack isolada, não à UI principal localhost:5000.

A rodada principal anterior permanece em [acceptance-v4.md](../v4/acceptance-v4.md).
Evidências novas não substituem os bytes ou IDs históricos daquela rodada.
Inspeção visual e CI remota permanecem não executadas. Não houve reset principal.

As valida??es AST/imports, depend?ncias fixadas, Compose gerado, links, lint F/E9 e
checagem de segredos passaram. Os notebooks executados est?o em `notebooks/` neste
diret?rio. Os fontes de runtime usados nos testes s?o identificados pelo hash de
c?digo em `isolated-final-proof.json`; documenta??o possui ?ndice SHA256 pr?prio.
