# Catálogo V4 do Workbench

Fontes versionadas nesta pasta; cópias editáveis em `workspace/notebooks`.
Reinício preserva edições. Mudança da fonte arquiva a cópia anterior em
`workspace/notebook-backups/`, mantendo uma entrada por notebook no catálogo ativo.

| Notebook | Função | Escrita |
|---|---|---|
| [00 ambiente](00_ambiente.ipynb) | SQL/MLflow e round-trip de artefato | Diagnóstico identificado |
| [01 fontes](01_fontes_academicas.ipynb) | Importação com proveniência | Referências SQL idempotentes |
| [02 qualidade](02_qualidade_dados.ipynb) | Grão, quarentena, códigos | Leitura |
| [03 exploração](03_exploracao_demanda.ipynb) | Histórico sintético por coorte | Snapshot determinístico SQL |
| [04 individual](04_treinamento_modelos.ipynb) | Um modelo por curso selecionado | Novo experimento/versão com NEW |
| [05 lotes](05_campanhas_lotes.ipynb) | Três cursos, checkpoints e métricas | Novo experimento/versões com NEW |
| [06 avaliação](06_avaliacao_modelos.ipynb) | Baseline e agregação | Leitura |
| [07 governança](07_governanca_registry.ipynb) | Revisão explícita | Apenas com APPROVE_DEMO |
| [08 publicação](08_publicacao_inferencia.ipynb) | Deploy e proposta operacional | Controles DEPLOY_DEMO / GENERATE |
| [09 aplicação](09_simulador_aplicacao.ipynb) | Tabela, filtros e atividades por HTTP | Leitura |
| [10 auditoria](10_auditoria_lineage.ipynb) | Confronto de versões e artefatos | Leitura |
| [11 reset](11_reset_poc.ipynb) | Orientação para reset seletivo | Run All não exclui; controlador externo executa |

Execute em kernel novo. Para proposta completa: 00→01→02→03→05→06→07→08→09→10.
04 é alternativa individual. 04/05 criam experimento a cada execução da célula de
treino em NEW; para recuperar ensaio existente, configure RESUME e sua chave.

08 salva o contexto para 09/10; override explícito de proposta é possível. Nova
campanha limpa a referência à proposta anterior. O reset seletivo limpa esse
contexto e preserva a origem SQL, permitindo retomar a partir de 04/05.

09/10 recuperam automaticamente a proposta única da campanha pela API. Se ela
ainda não foi gerada, exibem a pendência e os links para 07/08. Propostas anteriores
podem ser escolhidas explicitamente em um seletor, sem copiar UUID manualmente.
Sem seleção, as consultas ficam `NOT_EXECUTED`, não VERIFIED.

`legacy/` contém fontes antigas fora da distribuição ativa. Relatórios executados
ficam em `artifacts/reports`, sem preencher outputs destes fontes.
[Runbook](../docs/operations/POC_V4_MANUAL_RUNBOOK.md).
