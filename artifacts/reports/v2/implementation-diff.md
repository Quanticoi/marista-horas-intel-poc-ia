# V2 — diagnóstico antes da implementação

## Resultado da implementação e revisão

| Base anterior | Implementação validada |
|---|---|
| Notebook02 somente consultava | Gera pela API/worker e concilia resposta, SQL e S3 |
| Campanha era inventário | Jobs persistentes, checkpoints, controles e 30/500 treinos reais |
| Governança somente leitura | Pedido/revisão autenticados, aprovação, revogação e rollback explícitos |
| Lineage limitado | N:N por linha, busca reversa e grafo paginado com verificação de hashes |
| Notebook09 somente preview | Audita plano/resultado; dois resets executados externamente na stack isolada |
| Scripts de correção misturados em dev | Dev apenas com instruções; ferramentas e ensaios documentados em pastas próprias |

Aceite técnico V2: 16 critérios PASS, 79 testes e CI41903976793 aprovado.
Campanha final: 500 treinos reais em 310,72s; dois processos; dados sintéticos
compartilhados, sem alegação de 500 modelos em memória. Modelo principal v15,
1050 registros SQL,90 linhas persistidas e consultadas. Onze serviços saudáveis;
preservados69runs/49versões/12propostas anteriores. Revisão removeu dez scripts
obsoletos e33imports sem uso. Nenhum backup de banco novo; nenhum reset principal.
Detalhes e limites em [acceptance-v2.md](acceptance-v2.md).

## Registro inicial preservado

04/11/2026. Referência Git e hashes em inventory-before.json. Runtime Docker Compose.
Estado V1.1: jornada 01 real; 02 consulta contrato; 05 somente catálogo; 07 somente
leitura; 09 pré-visualização. Execução dos dez notebooks anteriores confirmada em
kernels novos, mas os caminhos opt-in ainda não constituem aceite V2.

P0: adicionar job de geração pela API/worker, idempotência transacional e reparo
de manifest; campanhas persistentes com checkpoints, concorrência e retomada.
Reutilizar proposal_generations/lines/usage, MLflow e o único serviço de inferência.
P1: governança autenticada, consultas de lineage, notebooks orientados a tarefas,
relatórios por execução, documentação e ensaios reais isolados.

Riscos: jobs duplicados/restart durante publicação de artefato; versionamento de
modelos não é transacional com PostgreSQL; aprovação exige conciliação de alias.
Preservar dados principais, backups existentes e credenciais; aplicar migration
primeiro na stack isolada. O usuário dispensou backup de banco durante a montagem
da POC (04/11/2026); nenhum backup novo foi executado. Nenhum reset principal será realizado.

Decisão de UX: pedido direto do usuário exige uma única jornada na lista, portanto
prevalece sobre sugestão V2 de arquivos .update. Backups exatos fora de notebooks;
reinício da mesma versão conserva edições. Atualização de fonte informa a cópia
arquivada. Não reintroduzir duplicatas.

V3/V4.4: fontes e leitura documentadas no diagnóstico V1.1 e FUNCTIONAL_COVERAGE.
Trabalho atual mantém regras demonstrativas, sem docente/horário/sala; dados
ausentes continuam nulos e critérios institucionais não avaliados.
