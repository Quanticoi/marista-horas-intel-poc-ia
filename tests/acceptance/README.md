# Ensaios de aceitação

Estes arquivos são ferramentas de teste, não serviços nem passos obrigatórios
para abrir o Jupyter. Execute comandos do host a partir da raiz do repositório.

| Arquivo | Finalidade e execução |
|---|---|
| `isolated_stack.py` | Gera Compose separado, sem portas publicadas; `python tests/acceptance/isolated_stack.py` |
| `failure_drills.py` | Pause/resume/cancel, falha MLflow/SQL e SIGKILL do worker; somente projeto isolado |
| `reset.py` | Dois resets reais e jornadas pós-rebuild; somente projeto isolado |
| `verify_reset.py` | Prova independente SQL/SDK/S3/HTTP; chamado dentro de tools pelo teste de reset |
| `preservation.py` | Captura referência e verifica runs/versões/propostas/modelo após rebuild; executado em tools |
| `collect_evidence.py` | Copia evidências reais da stack isolada para artifacts/reports/v2/isolated |

`failure_drills.py` e `reset.py` interrompem serviços **da stack de teste**.
Não são comandos de limpeza cotidiana. `preservation.py before` recusa
sobrescrever a referência existente. Os ensaios V2 dentro dos containers ficam
em `src/workbench/v2_*.py`: campanhas reais, notebooks, controles, negativos,
serving, geração e lineage. Cada um produz evidências identificadas.

Os caminhos `dev/*.py` que aparecem em relatórios antigos registram o comando
usado naquela data; não são os caminhos atuais.
