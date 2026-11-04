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
No 02/08 informe `PROPOSAL_ID` ou edite o parâmetro explícito; não se escolhe a
proposta mais recente automaticamente. No 09, gere primeiro o plano no terminal.
Relatórios executados ficam em `artifacts/reports`, sem preencher outputs nos fontes.

V2: configuração tipada `Parameters`; veja [exemplos e controles](../docs/operations/OPERATIONS_V2.md).
Relatórios detalhados em artifacts/reports/v2. Testes opt-in usam stack descartável;
Run All do09 nunca executa remoções.
