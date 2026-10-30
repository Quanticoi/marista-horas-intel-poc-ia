# Estado atual — 30/10/2026

## Decisão vigente

**100% Docker Desktop / Docker Compose, sem Rancher ou Kubernetes.** Reafirmada
pelo usuário em 30/10, substitui a exigência K8s do pedido de jornada. Não reativar
cluster legado. Ler este estado antes de tomar decisões; AGENTS.md registra isso.
Preservar .env, volumes, workspace, bancos, bucket e versões anteriores.

## Implementação e execução real

Jornada principal: notebooks/01_jornada_completa_planilha_turmas.ipynb. Reaproveitados
módulos journey, SQL parametrizado, seed42, migration004, MLflow3.11.1 proxy,
inferência existente, proposta DRAFT transacional/idempotente e API PostgreSQL.
Corrigidos isolamento do teste de falha MLflow, diagnóstico em falha de tracking,
ordem init/testes e geradorCompose (antes perdia configurações da jornada).
README/guia JOURNEY/spec atualizados. JUPYTER_TOKEN vazio recuperado do container,
sem exposição ou rotação das outras credenciais.

Execução real Docker: rebuild PASS, acceptance PASS, test PASS. Notebook executado
em kernel novo: 1050 linhas SQL; Ridge fit/predict; MAE3.7586306583/RMSE4.9142272797;
90 propostas persistidas/reconciliadas pela API. Dados DEMO, sem mérito real alegado.

Execução/correlação/proposta: a741d0dd-d1ed-41eb-91d1-d5194c5fb692.
Run: ad2530361ab14f7d87017c21d11958a1; experimento4; planilha-turmas-demo versão3.
Mesma run/versão/proposta conferida após restartMLflow e rebuild:7PASS em cada fase.
BytesS3=proxy, idempotência, rollback, auth e eventosdashboard testados.
Suíte geral37PASS;19checksHTTP PASS; pipcheck/dependênciasPASS; geradorComposecheckPASS.

Evidência principal: artifacts/reports/journey-acceptance-2026-10-30.md;
notebook executado, journey-latest.json, journey-{junit,after-restart,after-rebuild}.xml,
compose-junit.xml e access-check.json no mesmo diretório. Sem segredos do .env nas
evidências da jornada verificadas.

## Operar e pendências

compose.ps1 start/status/journey para uso diário; rebuild preserva volumes;
acceptance verifica mesma execução após restart/rebuild. Credenciais no .env.
Jupyter localhost8888 (notebooks/01_jornada_completa_planilha_turmas.ipynb, editável);
MLflow5000, API8000/docs, dashboard8088, RustFS9001. Não executar down -v.

Pendente: inspeção visual MLflow (browser access host unavailable; SDK/HTTP PASS),
instalação com volumes vazios e execução Bash/Linux não testadas nesta sessão.
FonteREAL, regrasMER, homologação, produção e aprovação/publicação operacional
permanecem fora do aceite DEMO. Nenhum modelo promovido por esta jornada.
Sem commit/push; arquivos do projeto continuam não versionados no índice Git.

## Histórico anterior (não substitui os resultados atuais)

# Estado atual ? C3 28/10/2026
SDK Jupyter HTTP/S3 sem senhaPG; ingestion8020; PostgreSQL ?nicoSGBD; bin?rios MLflow+SHA, sem fit na infer?ncia; migra??o003/proveni?ncia; API/container por modelo aprovado via publish. Notebook09/workspace adicionado; antigos preservados. Docs/CI/Compose atualizados.
Valida??o:26unitPASS; integra??o isolada2vers?es/PGRustFS/promo??o/API/troca/rein?cio/upgradePASS; artifacts/reports/c3-*. Original36modelos/0aliases preservado. DaemonDocker negado: aplicar build?migrate?start?validate; revisar/aprovar/publicar candidato. Branchdevelopment semcommit/push. GCP/TLS/ArtifactRegistry pendentes.
Tempor?rios .runtime/c3-venv e workspace/.c3-validation preservados: exclus?o recusada pela revis?o autom?tica (aprova??o indispon?vel).

## Registro anterior

# Estado — revisão 26/10/2026

Estratégia: Compose local, Helm como base futura. Repo Quanticoi/marista-horas-intel-poc-ia; development→staging→main homologada; arquivos ainda sem commit/push.
Migração anterior PASS:19testes,39runs,36modelos/versões,124objetos. K8s5namespaces/5PVs removidos; imagens antigasRancher mantidas por restrições. Backup .runtime/migration + .env preservados.
Revisão atual:20arquivos obsoletos removidos(10scripts Rancher,5Dockerfiles,4YAMLsemuso,1guia); migração isolada deployment/migration; Compose.ps1 diário init/build/start/stop/restart/status/logs/check/validate/test sem depender backup.
DocsREADME/instalação/operação/arquitetura atualizados; docs/REPOSITORY_REVIEW.md contém decisões e próximos passos. ChartsHelm/collector preservados para futuro, não prontos produção.
Runtime: endpoints por env, sem aliasesDNSK8s noCompose; dashboard Ambiente; tools recebe DASHBOARD_TOKEN paraE2E. GeradorHelm não reescreve notebooks. Nenhuma célula/notebook/workspace modificada ou executada.
Verificação atual: AST57/9notebooks/DDL/links/Composegraph+health+secrets+mounts/config/PS/Bash/JS PASS;2testes retomadaarquivoPASS.2testes dashboard adicionados para próximo build.19PASS é evidência pré-revisão.
Bloqueio sessão: leitura dockercontext/daemon negada. Necessário usuário compose.ps1 build e validate para aplicar/testar revisão.
Próximos: validarbuild→revisarnotebooks/datasetcomusuário→aprovaçãomodelos/E2E→backupexterno/homologação→publicarGitCI→staging→main. Preservar nomes bucket/experimentos para integridade e planejar CODE_VERSION/imagestags imutáveis antesstaging.
ATUALIZAÇÃO ACESSOS26/10:17checksHTTP reais PASS (MLflow/API/dashboard/Jupyter/Rabbit/monitor/RustFSconsole+S3/inferência/tokennegativos). artifacts/reports/access-check.json sem credenciais. .env recebeu comentários de loginRustFS mantendo valores. docs/operations/ACESSOS.md contém mapa completo.
Limpeza complementar: ferramentas migração/helpers+27arquivosobsoletos/12logsforward removidos; sem mounts .runtime/migration noCompose. Backups originais, .env, workspace/notebooks, relatórios atuais e Helm úteis preservados. Algumas pastasvazias permanecem: exclusão bloqueada revisãoautomática/sandboxaprovaçãoindisponível. check_access.py integrado validate/CI, requer Pythonstdlibhost. AST54/links/composeconfig/PSparserPASS; rebuild da revisão ainda depende terminalusuário.

Atualização 30/10 — notebook editável: usar /lab/tree/notebooks/01_jornada_completa_planilha_turmas.ipynb (Contents API confirmou writable=true). /templates é referência somente leitura. Cópia workspace preservada, igual ao template na verificação. Aviso Git não impede treino; falta executável no container para SHA automático, code_version registra hash do código.
