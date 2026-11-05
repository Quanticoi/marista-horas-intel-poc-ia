# Ensaios de aceitação

## V4 atual

| Ferramenta | Finalidade |
|---|---|
| `isolated_stack.py` | Gera projeto `marista-correcoes-isolated`, sem portas de host |
| `v4_adjustments.py --reset-isolated` | Dois experimentos, retomada explícita, reset seletivo e treino pós-reset sem reimportação |
| `v4_campaign_policy.py` | Parte executada dentro do Workbench pelo ensaio acima |
| `v4_evidence.py` | Audita a proposta do contexto explícito; não treina |
| `v4_restart.py` | Verifica recuperação PRELOAD/LAZY; leia as pré-condições no código |
| `v4_editability.py` | Grava/relê/remove apenas notebook temporário de teste |
| `v4_operational.py` | Aprovação técnica DEMO, deploy e geração explícitos |

`python -m src.workbench.v4_notebook_suite --approve-demo` roda 12 notebooks em
kernels novos dentro do Jupyter, com escritas DEMO explícitas. Sem o opt-in não
aprova/publica. [Runbook](../../docs/operations/POC_V4_MANUAL_RUNBOOK.md).

## Ferramentas históricas

Arquivos `report_v3`, `probe_v3`, `inventory_v3`, `preservation_v3`, `failure_drills`,
`reset.py` e os coletores anteriores correspondem aos contratos V2/V3. Não são
os critérios de aceite do treinamento V4. São preservados para interpretar/reproduzir
as provas históricas; não execute rotinas antigas de treinamento operacional.
