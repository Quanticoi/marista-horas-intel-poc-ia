# Entrega V3 — pronta para teste local

Gerado em 2026-11-04T21:59:49.667302+00:00. **Implementação finalizada; 85 testes passaram, zero falhas.** Conforme orientação do usuário, a conferência local fica a seu cargo. UI e CI remoto não impedem esta entrega; a matriz mantém os resultados efetivamente executados.

Base Git: `b02739caf75c202402332c04b3c626dd1fa9eb40`. V3 ainda não commitada. Código da imagem principal verificada: `sha256:c02b59b92e12bc01b01745cc19d2818552f15868d4852fc6891dcad2aa88f1dd`.

[JSON completo](acceptance-v3.json) · [Roteiro manual](../../../docs/operations/MANUAL_ACCEPTANCE_V3.md) · [SQL](../../../docs/operations/SQL_VALIDATION_V3.md)

| Critério | Estado | Evidência e alcance |
|---|---|---|
| V3-01 | AUTO_PASS | [Onze serviços healthy; diagrama de startup preservado.](runtime-after.json) |
| V3-02 | MANUAL_NOT_CHECKED | [SDK comprova nomes/tags/Registry; UI exige observação real registrada.](ui-observations.json) |
| V3-03 | AUTO_PASS | [Treino e repetição idempotente em kernel novo, tabela Onde conferir.](isolated/notebooks/04-train.ipynb) |
| V3-04 | AUTO_PASS | [Campanha real com 30 escopos DEMO; default manual permanece três.](isolated/notebooks/05-campaign-30.ipynb) |
| V3-05 | AUTO_PASS | [Catálogo imutável aponta para três arquivos originais; sem duplicar binário.](scenario-latest.json) |
| V3-06 | AUTO_PASS | [Comparação byte a byte proxy/S3, hash Registry/catálogo e assinatura.](main-suite-junit.xml) |
| V3-07 | AUTO_PASS | [Quatro views e consultas parametrizadas; nove ofertas com três contribuições.](main-suite-junit.xml) |
| V3-08 | AUTO_PASS | [Auditoria reversa verifica run/versão/snapshot/manifests/atribuição de linhas.](scenario-latest.json) |
| V3-09 | AUTO_PASS | [Geração HTTP por API/worker e conferência SQL, sem treino no notebook02.](isolated/notebooks/02-generate.ipynb) |
| V3-10 | AUTO_PASS | [Jupyter parado; cache vazio após restart; três modelos recarregados.](isolated/serving.json) |
| V3-11 | AUTO_PASS | [Rebootstrap empty saudável sem modelos; saúde/registro/cache/aprovação distintos.](reset-isolated-proof.json) |
| V3-12 | AUTO_PASS | [Revisão explícita DEMO; revogação bloqueia APPROVED com cache quente.](isolated/negative.json) |
| V3-13 | AUTO_PASS | [Histórico preservado; versões sem catálogo completo permanecem LEGACY_PARTIAL.](preservation-after.json) |
| V3-14 | AUTO_PASS | [Três períodos DEMO distintos, três SHA256 e segunda versão com alpha diferente.](scenario-latest.json) |
| V3-15 | MANUAL_NOT_CHECKED | [Roteiro completo e pacote JSON/Markdown/CSV; inspeção de todas as interfaces ainda necessária.](ui-observations.json) |
| V3-16 | AUTO_PASS | [Artefatos/tags/assinatura/manifest divergentes, snapshot errado, versão ausente, auth e revogação rejeitados.](isolated/negative.json) |
| V3-17 | NOT_EXECUTED | [CI remoto não executado e fora do fechamento local solicitado pelo usuário. Pipeline contém testes novos; nenhum commit/PR foi criado.](../../../.github/workflows/compose.yml) |
| V3-18 | AUTO_PASS | [Estados automáticos, manuais e bloqueados separados; nenhum 20/20 fabricado.](acceptance-v3.json) |
| V3-19 | AUTO_PASS | [Reset-data/empty e factory-reset/demo-ready somente isolados; arquivos protegidos conferidos.](reset-isolated-proof.json) |
| V3-20 | AUTO_PASS | [83 runs, 57 versões, 395 objetos, 22 propostas e dez notebooks anteriores preservados.](preservation-after.json) |

## Sessão principal disponível para conferência

Proposta: `ca4539df-4a11-4647-9d77-2cc36a484968`; campanha: `4626d239-6145-4cc3-95ca-5640799dff03`; snapshot: `fb931e1e-43d0-5ff8-938c-0d2ba4a68794`.

| Modelo DEMO | Versão | Run / Registry | Manifest |
|---|---|---|---|
| hi.pt.demanda.DEMO-C1.DEMO-CR1.P1 | 4 | [Run 18cdc4f1](http://localhost:5000/#/experiments/5/runs/18cdc4f10eaf47e4ab30104994e34ca5) · [Registry](http://localhost:5000/#/models/hi.pt.demanda.DEMO-C1.DEMO-CR1.P1/versions/4) | `s3://pucpr-poc/lineage/poc/planilha-turmas/catalog/cycles/2026-1/models/hi.pt.demanda.DEMO-C1.DEMO-CR1.P1/versions/v0004/manifest.json` |
| hi.pt.demanda.DEMO-C1.DEMO-CR1.P2 | 2 | [Run efeccb74](http://localhost:5000/#/experiments/5/runs/efeccb749af2422f84df5f1b43153f43) · [Registry](http://localhost:5000/#/models/hi.pt.demanda.DEMO-C1.DEMO-CR1.P2/versions/2) | `s3://pucpr-poc/lineage/poc/planilha-turmas/catalog/cycles/2026-1/models/hi.pt.demanda.DEMO-C1.DEMO-CR1.P2/versions/v0002/manifest.json` |
| hi.pt.demanda.DEMO-C1.DEMO-CR2.P1 | 2 | [Run 626ab2a7](http://localhost:5000/#/experiments/5/runs/626ab2a7935248baae5285af455acb9a) · [Registry](http://localhost:5000/#/models/hi.pt.demanda.DEMO-C1.DEMO-CR2.P1/versions/2) | `s3://pucpr-poc/lineage/poc/planilha-turmas/catalog/cycles/2026-1/models/hi.pt.demanda.DEMO-C1.DEMO-CR2.P1/versions/v0002/manifest.json` |

## Alterações e persistência

- HI-LINEAGE/1.1: nomes por códigos sintéticos reais, experimento por ciclo, tags coerentes e versão explícita.
- planning.model_version_catalog + quatro views; dados de negócio permanecem em planejamento_db. mlflow_db continua exclusivamente administrado pelo MLflow.
- RustFS mantém binários originais em mlflow/ e catálogo legível em lineage/. Manifests são condicionais e imutáveis.
- Auditoria autenticada, filtros no dashboard, dez notebooks e exportação de sessão com links diretos e CSV de objetos.
- Assinatura/hash validados antes da desserialização; tags conferidas mesmo com cache quente; limite de quatro versões por processo.

## Executar e reproduzir

```powershell
.\deployment\scripts\compose.ps1 start
# Para aplicar alterações futuras, preservando dados:
.\deployment\scripts\compose.ps1 rebuild
# Conferir testes:
.\deployment\scripts\compose.ps1 test
python tests/acceptance/jupyter_editability.py --report-version v3
python tests/acceptance/report_v3.py
```

Abra [Jupyter](http://localhost:8888), execute 00; use 04/05 para treino, 02 para geração e 08 para auditoria. 01 continua demonstração legada. Configuração de escrita explícita no roteiro manual.

[MLflow](http://localhost:5000) · [RustFS](http://localhost:9001) · [API](http://localhost:8000/docs) · [Dashboard](http://localhost:8088)

## Limitações e pendências

- Base Git b02739caf75c202402332c04b3c626dd1fa9eb40 com alterações locais: não é um commit que contenha a V3. Não houve commit, push ou PR.
- Cada prova conserva sua data e versão de código; resets ocorreram antes do reforço final da auditoria. Migração e controlador não mudaram depois do ensaio.
- Por orientação posterior do usuário, a entrega é do código pronto para teste local. Conferência visual fica com o usuário; CI remoto não é condição para esta entrega. Nenhum resultado não executado foi marcado PASS.
- 500 ensaios V2 são baseline histórico de orquestração sobre o mesmo dataset/um SHA; não certificam V3 ou 500 comportamentos. V3 executou campanha de 30 escopos e prova de três modelos distintos.
- DEMO e contrato provisório; V4.4, PRIME, dados reais, produção/GCP e SLO não homologados.
- Catálogo SQL 1.1 indexa novas versões. Registro antigo sem contexto suficiente não recebe backfill inventado; consultar Registry/lineage e LEGACY_PARTIAL.
- O inventário anterior não continha aprovações: nenhuma aprovação histórica principal foi exercitada na prova de preservação; governança foi testada no isolado.
