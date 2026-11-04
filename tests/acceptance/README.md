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
| `jupyter_editability.py` | Salva/relê um notebook temporário pela API e o remove; confere o catálogo editável |
| `report.py` | Consolida as provas existentes; evidência ausente nunca recebe PASS |
| `inventory_v3.py` | Inventário anterior somente leitura; executado em tools com /repository:ro; recusa sobrescrever baseline |
| `preservation_v3.py` | Compara baseline V3 com SQL/SDK/S3 e cópias editáveis/arquivadas; tools com PYTHONPATH=/app |
| `probe_v3.py` | Serving sem Jupyter, falhas de artefatos/tags/assinatura/manifest e MLflow down; somente projeto isolado |
| `report_v3.py` | Consolida matriz V3-01..20 e índice SHA dos arquivos; não inventa PASS manual ou CI |

V3: `reset.py --report-version v3` e `jupyter_editability.py --report-version v3`
mantêm evidências separadas da V2. Os notebooks atuais exportam em `/reports/v3`.
Use [o roteiro manual](../../docs/operations/MANUAL_ACCEPTANCE_V3.md) e consulte
[o relatório final](../../artifacts/reports/v3/acceptance-v3.md) para limites das provas.

`failure_drills.py` e `reset.py` interrompem serviços **da stack de teste**.
Não são comandos de limpeza cotidiana. `preservation.py before` recusa
sobrescrever a referência existente. Os ensaios V2 dentro dos containers ficam
em `src/workbench/v2_*.py`: campanhas reais, notebooks, controles, negativos,
serving, geração e lineage. Cada um produz evidências identificadas.

Os caminhos `dev/*.py` que aparecem em relatórios antigos registram o comando
usado naquela data; não são os caminhos atuais.
