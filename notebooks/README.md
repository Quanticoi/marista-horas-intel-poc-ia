# Catálogo do Workbench

Fontes versionadas nesta pasta. Cópias editáveis em `workspace/notebooks`, publicadas
no início do Jupyter. Uma edição existente nunca é sobrescrita: atualização conflitante
recebe sufixo `.update-<hash>`. Compare e incorpore as mudanças desejadas.

| Notebook | Propósito | Escritas/risco |
|---|---|---|
| 00_validacao_ambiente | Dependências SQL/MLflow/artefatos | Run diagnóstica identificada |
| 01_jornada_completa_planilha_turmas | Jornada completa em kernel novo | Treina, registra e cria nova proposta DRAFT |
| 02_teste_inferencia_planilha_turmas | JSON HTTP, regras, SQL, Registry e RustFS | Somente relatórios; POST DEMO opt-in |
| 03_exploracao_preparacao_dados | SQL e separação temporal | Leitura |
| 04_treinamento_individual | Chave e snapshot explícitos | Treino opt-in, nunca promoção |
| 05_treinamento_campanha | Inventário real | Leitura; scheduler persistente NOT_IMPLEMENTED |
| 06_avaliacao_comparativa | Métricas de runs | Leitura |
| 07_registry_governanca | Versões e estado operacional | Leitura; promoção externa exige operador/razão |
| 08_auditoria_lineage | Navegação por identidade | Leitura, identificador obrigatório |
| 09_reset_total_ambiente_poc | Inspeção de plano e comando externo | Run All não executa exclusão |

Ordem sugerida: 00 → 01 → 02 → 08. Use 03–07 conforme a atividade científica.
No 02/08 informe `PROPOSAL_ID` ou edite o parâmetro explícito; não se escolhe a
proposta mais recente automaticamente. No 09, gere primeiro o plano no terminal.
Relatórios executados ficam em `artifacts/reports`, sem preencher outputs nos fontes.
