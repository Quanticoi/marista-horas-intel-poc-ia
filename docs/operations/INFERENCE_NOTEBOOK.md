# Notebook de inferência/contrato

Abra `02_teste_inferencia_planilha_turmas.ipynb`. Informe `execution_id` usando a
lista controlada por ciclo ou configure PROPOSAL_ID. Execute desde o início.
Sem ID a execução interrompe de forma explícita; não escolhe arbitrariamente.

O fluxo testa health/OpenAPI/autenticação, lê o JSON HTTP paginado, valida schema
e hashes, mostra todas as ofertas, regras PASS/FAIL/NOT_EVALUATED, lê SQL por nova
conexão e compara os binários via MLflow e RustFS. Negativos401/404/schema/hash
não alteram propostas. Relatórios `inference-contract-<id>.json/.md`.

`invoke_demo_inference=False` é o padrão. Habilitar a opção chama a API de
inferência com versão/snapshot explícitos, sem treinar ou escrever a proposta.
É uma nova invocação com inference_id próprio, não uma revisão de negócio.

Execução automatizada no container:
```powershell
docker compose exec -T jupyter /usr/local/bin/_entrypoint.sh python -m src.workbench.execute_notebook 02_teste_inferencia_planilha_turmas.ipynb --proposal-id <UUID>
```
