# Atualização — 03/11/2026: limpeza implementada e verificada

## Tracing e provas de persistência — implementação atual

Pedido do usuário: adicionar Traces e esclarecer repetição, experimentos, storage,
banco de negócio e organização de 500 modelos. Implementados traces por tentativa
de etapa, contexto W3C Jupyter/API/inferência, spans SQL/carga/predição, captura
somente de metadados, tags execution_id/run/modelo. Destino remoto configurado antes
de adotar contexto; primeira validação detectou spans NoOp, corrigido e retestado.
Etapas 7b e 10b provam hashes RustFS/proxy e todas as linhas via nova conexão SQL.
Experimento configurável pelo .env, mesmo destino em Jupyter/API/inferência.
Notebook fonte e cópia editável atualizados; gerador correspondente --check PASS.
Guia: docs/operations/EXPERIMENTS_AND_TRACING.md. Organização de 500 modelos é
proposta documentada: não executados 500 treinos nem implementado orquestrador
de campanhas ou schema de geração com vários modelos.

Rebuild/deploy Docker e notebook completo em kernel novo PASS. Execução
d6260507-b9f4-4011-a3f6-b3dd511400d5; run 03012b122e6143b2919807cd91973451;
modelo planilha-turmas-demo v8, experimento 4; 1050 linhas SQL, 90 propostas/API.
12 traces e 21 spans, incluindo filhos reais de API/inferência. Três arquivos do
modelo comparados por SHA256 com RustFS; proposta DRAFT conferida linha a linha.
10 testes da jornada PASS; suíte geral 44 PASS; 19 checks HTTP PASS.
Falha controlada/repetição testadas sem registrar payload de erro sensível.
Links conferidos no código da UI instalada: selectedEvaluationId + compareRunsMode.
Evidências em tracing-acceptance-2026-11-03.md, journey-latest.json e JUnit.
Volumes/dados anteriores preservados. Limpeza MLflow continua sem exclusões,
aguardando decisão sobre preservação de histórico. Informações abaixo são históricas.

Teste manual: repetição da etapa register falhava com NameError após del model.
Corrigidos notebook fonte e célula correspondente no workspace, sem alterar demais
células/outputs. register agora recupera versão já registrada e verifica run/modelo/
execution_id; objeto ausente ou run incorreta bloqueiam novo registro. step informa
NameError.name sem expor mensagem arbitrária. Três regressões PASS e repetição real
da versão 6 duas vezes PASS, sem criar run/versão. Build das duas imagens PASS;
arquivos também aplicados ao container Jupyter sem reiniciar kernel do usuário.
Kernel já aberto mantém funções antigas até reload/restart; pode seguir etapa 8
com trace da versão 6. Relatório register-repeat-junit.xml.

MLflow: inventário em mlflow-inventory-2026-11-03.json. 9 runs/6 modelos do lab
macroeconômico, 7 runs diagnósticas, 30 modelos acadêmicos vinculados ao catálogo,
6 versões Planilha Turmas (1..5 vinculadas a propostas; 6 do teste manual atual).
Nenhuma exclusão aplicada; aguardando escolha do usuário entre limpeza preservando
rastreabilidade ou reset total. Traces não instrumentados: apenas Runs e eventos
JSONL; variável trace é dicionário de IDs, não MLflow Trace. Explicação documentada.

Correção posterior ao teste manual: Git ausente causava WARNING no MLflow.
Dockerfiles Jupyter/aplicação agora instalam Git; ambas imagens reconstruídas.
Git 2.39.5 instalado também no Jupyter ativo sem reiniciar sua sessão. GitPython
e get_git_commit('/app') validados no container ativo e em containers isolados
das duas imagens: PASS, sem warning. /app não é clone Git; code_version continua
SHA256 dos fontes. Não usado GIT_PYTHON_REFRESH=quiet. Imagens novas disponíveis
para próxima recriação; correção já aplicada ao Jupyter atual. Sem novo treino
para esta alteração de dependência. Usuário pode reiniciar apenas o kernel se
quiser uma execução limpa, após salvar o notebook.

Usuário solicitou retirar notebooks antigos e itens fora do escopo da jornada.
Somente Jornada Completa permanece em notebooks/ e workspace/notebooks/; 21 cópias
antigas arquivadas em .runtime/notebooks-archive-20261103-101931. Edições da Jornada
e notebooks pessoais Untitled preservados. Atalhos Markdown:Shift+Enter renderiza;
Ctrl+Enter renderiza sem mudar célula;Ctrl+S salva.

Removidos 36 alvos sem uso (inventário artifacts/reports/cleanup-2026-11-03.json):
pastas vazias de data; Helm/Kubernetes/gerador; collector/config logging;
laboratório público; venv/helpers/cópias de validação antigas. Bancos, volumes, .env,
backups e evidências acadêmicas preservados. Dashboard desacoplado Kubernetes;
configuração Jupyter passa a abrir apenas notebook editável,sem mounttemplates.
Validação estática de 78 fontes Python, SQL, notebook, links e Compose: PASS.
Build das duas imagens: PASS. Suíte: 37 testes PASS; 19 verificações HTTP PASS.
Imagem Jupyter nova: somente notebook principal e SDK Kubernetes ausente, PASS.
Container atual: /app/notebooks contém somente notebook principal, conferido.
Após autorização do usuário, compose.ps1 rebuild executado em 03/11: imagens
aplicadas e containers da aplicação/Jupyter recriados; 11 serviços saudáveis.
Volumes preservados. SHA256 do notebook editável igual antes/depois:
63F164ECAD07442D61E06B98F8356281541A6699C56BD1DD108CABA36396CDFB.
API Jupyter confirma writable=true após recriação. Não há restart pendente.
Jornada executada em kernel novo: 1050 linhas SQL, 90 propostas/API, modelo
planilha-turmas-demo versão 5; execução 46b6b778-3c52-4e15-ac52-3d3c5d5939a5;
run 1d62be545bed47c7b3f8847159fd7ff4, experimento 4. Sete testes da jornada e
19 checks HTTP PASS. Evidências atualizadas em artifacts/reports/journey-latest.json,
journey-junit.xml, notebook executado e jupyter-after-rebuild-2026-11-03.json.

## Estado anterior
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
Publicado em https://github.com/Quanticoi/marista-horas-intel-poc-ia. Branch padrão development; código no commit 3727d394303b48bee7470d6870a09eb9cd78eb54. staging e main reservadas na base vazia 779f827c3fd18e79e05e9e9cd4c12d8aeaa8a9f3, sem promoção. CI remoto deve ser consultado separadamente dos testes locais.

## Revisão da documentação — 30/10/2026

README reescrito como entrada técnica: finalidade, arquitetura Mermaid, onze
componentes, instalação Windows, atualização, Jupyter editável, etapas, dados/modelo,
persistência, configuração, APIs, operação, validação e diagnóstico. Guias de
arquitetura/dados/operação alinhados a SQL direto e MLflow proxy; fluxo complementar
por série identificado separadamente. Documentação pública deve explicar o produto
e sua operação; decisões históricas como exclusão de um runtime ficam no histórico,
não como slogans na apresentação. Validação estática/links e git diff --check PASS.
Alteração documental; nenhum serviço reiniciado nem teste funcional reexecutado.
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

Atualização 03/11 — Jupyter: API confirmou sessão ativa da Jornada Completa em templates/ (somente leitura); cópia em notebooks/ editável e sem bloqueios nas células. Abrir /lab/tree/notebooks/01_jornada_completa_planilha_turmas.ipynb. Demais notebooks preservados; nenhum arquivo excluído.
