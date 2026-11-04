# V2 — diagnóstico antes da implementação

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
