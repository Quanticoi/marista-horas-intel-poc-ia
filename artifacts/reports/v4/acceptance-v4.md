# Aceite V4 - importacao das planilhas

V4 NAO CONCLUIDA. Tres planilhas importadas; quatro PDFs recebidos/conferidos, diagnostico ainda ausente. 29 testes PASS em simulation-junit.xml. Simulacao persistida; sem treino ou E2E V4.

| Critério | Estado | Evidência / limitação |
|---|---|---|
| V4-01 | AUTO_PASS | import-report.json, source-mapping.csv, academic-import-junit.xml: origens conservadas, cursos distintos, P164 e P110A; duplicatas em quarentena. |
| V4-02 | AUTO_PASS | import-report.json, source-mapping.csv, academic-import-junit.xml: origens conservadas, cursos distintos, P164 e P110A; duplicatas em quarentena. |
| V4-03 | AUTO_PASS | import-report.json, source-mapping.csv, academic-import-junit.xml: origens conservadas, cursos distintos, P164 e P110A; duplicatas em quarentena. |
| V4-04 | AUTO_PASS | import-report.json, source-mapping.csv, academic-import-junit.xml: origens conservadas, cursos distintos, P164 e P110A; duplicatas em quarentena. |
| V4-05 | NOT_EXECUTED | Arquivo real: 31 entidades/175 campos; divergencia da SPEC registrada. Metadados de prontidao preservados; conformidade integral pendente. |
| V4-06 | AUTO_PASS | scenario-manifest.json e simulation-junit.xml: seed, coortes, categorias, calendario, determinismo e persistencia SQL. |
| V4-07 | NOT_EXECUTED | Dependente das fontes acadêmicas; source_inventory.json registra SOURCE_MISSING. |
| V4-08 | NOT_EXECUTED | Dependente das fontes acadêmicas; source_inventory.json registra SOURCE_MISSING. |
| V4-09 | NOT_EXECUTED | Dependente das fontes acadêmicas; source_inventory.json registra SOURCE_MISSING. |
| V4-10 | NOT_EXECUTED | Dependente das fontes acadêmicas; source_inventory.json registra SOURCE_MISSING. |
| V4-11 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-12 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-13 | NOT_EXECUTED | Catálogo e matemática têm 12 testes unitários aprovados em foundations-junit.xml; integração Jupyter/MLflow não executada. |
| V4-14 | NOT_EXECUTED | Catálogo e matemática têm 12 testes unitários aprovados em foundations-junit.xml; integração Jupyter/MLflow não executada. |
| V4-15 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-16 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-17 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-18 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-19 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-20 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-21 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-22 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-23 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-24 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |
| V4-25 | NOT_EXECUTED | Fluxo V4 ainda não implementado/validado ponta a ponta. |

Checklist visual por componente: **MANUAL_NOT_CHECKED**. Não reutilizar evidências V3 como PASS V4.

Prova independente: inventário de fontes e oito métricas, 12 testes PASS em container sem rede. Esta prova não satisfaz sozinha V4-13/14. Código base: 9ff5a808cf76d3b34f568892a34aa07dbf846f3e mais alterações locais do checkpoint. Dados dos testes: arrays unitários SYNTHETIC, sem origem institucional. Configuração: catalog/profile 1.0; sem seed (arrays fixos), sem contrato de aplicação V4 gerado.
