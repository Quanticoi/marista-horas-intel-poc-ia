# Catálogo do Workbench

Fontes versionadas nesta pasta. Cópias editáveis em `workspace/notebooks`, publicadas
no início do Jupyter. Reiniciar a mesma versão preserva edições. Uma atualização
da fonte arquiva a cópia editada em `workspace/notebook-backups/` antes de atualizar
o arquivo principal; não cria duplicatas na lista do Jupyter.

| Notebook | Propósito | Escritas/risco |
|---|---|---|
| 00_validacao_ambiente | Dependências SQL/MLflow/artefatos | Run diagnóstica identificada |
| 01_jornada_completa_planilha_turmas | Jornada completa em kernel novo | Treina, registra e cria nova proposta DRAFT |
| 02_teste_inferencia_planilha_turmas | READ_EXISTING ou GENERATE_AND_VALIDATE via API/worker | Geração persistida opt-in; validação SQL somente leitura |
| 03_exploracao_preparacao_dados | SQL e separação temporal | Leitura |
| 04_treinamento_individual | Chave e snapshot explícitos | Treino opt-in, nunca promoção |
| 05_treinamento_campanha | Criar/acompanhar/pausar/retomar/cancelar/reprocessar campanhas | Jobs reais opt-in; estado/checkpoint PostgreSQL |
| 06_avaliacao_comparativa | Métricas de runs | Leitura |
| 07_registry_governanca | Solicitação/revisão/aprovação/revogação/rollback | Leitura padrão; decisão exige credencial separada e confirmação |
| 08_auditoria_lineage | Navegação por identidade | Leitura, identificador obrigatório |
| 09_reset_total_ambiente_poc | Inspeção de plano e comando externo | Run All não executa exclusão |

Ordem sugerida: 00 → 01 → 02 → 08. Use 03–07 conforme a atividade científica.
No 02, READ_EXISTING continua automaticamente a jornada 01 concluída: usa
`/workspace/reports/journey-current.json` e valida ciclo, run, snapshot e versão
na API antes de consultar. Instalações anteriores usam `/reports/journey-latest.json`
quando o novo contexto ainda não existe. Não pesquisa a proposta mais recente no banco.
Um `PROPOSAL_ID` explícito tem prioridade. No 08 informe o ID da entidade.
No 09, gere primeiro o plano no terminal.
No 02, a célula **1.1** permite preencher `selection` diretamente: para leitura,
use `{"mode": "READ_EXISTING", "proposal_id": "UUID da tabela"}`. Esse UUID é
o `execution_id` apresentado pela jornada 01. Para nova inferência, preencha o
exemplo `GENERATE_AND_VALIDATE` na mesma célula com snapshot, modelo, versão e
confirmação de escrita. Leitura não executa nova inferência. Sem contexto válido
ou seleção manual, o notebook pede uma seleção; não inicia geração silenciosa.
Relatórios executados ficam em `artifacts/reports`, sem preencher outputs nos fontes.

V2: configuração tipada `Parameters`; veja [exemplos e controles](../docs/operations/OPERATIONS_V2.md).
Relatórios detalhados em artifacts/reports/v2. Testes opt-in usam stack descartável;
Run All do09 nunca executa remoções.
