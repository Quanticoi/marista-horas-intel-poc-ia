# Notebook02 — gerar ou consultar proposta pela API

O modo padrão READ_EXISTING usa proposal_id explícito. GET autenticado/paginado
valida Pydantic, hash, IDs, quantidades SQL, snapshot, versões e bytes RustFS.
Nenhuma proposta é selecionada implicitamente por ser a mais recente.

GENERATE_AND_VALIDATE exige snapshot, modelo/versão, capacidade DEMO, solicitante,
request_key e confirmação EXECUTE_DEMO. O notebook chama POST /v1/proposals/generations,
recebe202, acompanha job/status, recebe proposal_id e executa a mesma validação GET.
Não chama persist nem escreve tabelas. A escrita pertence ao worker.

Mesma chave/payload retorna mesmo job; alteração retorna409. Nova chave cria outra
proposta, preservando as anteriores. O endpoint /internal/draft/predict continua
compatível, mas não é confundido com criação de proposta.

O payload integral fica visível no notebook e no relatório. Estudantes por origem,
coorte/turno e regras não demonstradas continuam null/NOT_EVALUATED. Capacidade40
é substituível por parâmetro, não uma decisão institucional.

[Configuração, rotas e exemplos](OPERATIONS_V2.md). Executor:

```powershell
docker compose exec -T jupyter /usr/local/bin/_entrypoint.sh python -m src.workbench.execute_notebook 02_teste_inferencia_planilha_turmas.ipynb --proposal-id <UUID>
```

Os parâmetros V2_* podem ser fornecidos ao processo para o modo opt-in. Nunca
inclua tokens nos parâmetros. Relatórios em artifacts/reports/v2; execução de
escritas/carga/governança de aceite somente em stack descartável.
