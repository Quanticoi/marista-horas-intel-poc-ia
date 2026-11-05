# 05/11/2026 — V4: três planilhas importadas; fontes documentais ainda ausentes

Usuário indicou dev: três planilhas presentes, copiadas para data/reference somente leitura e SHA256 conferidos. Leitura XML OOXML sem macros/links/fórmulas executadas. Migração010 aditiva aplicada em container tools; importação em transação concluída no PostgreSQL: 3 fontes, 107 linhas (82+25), 70 chaves de oferta, 175 campos. Arquivo real contém 31 entidades, não 30 da SPEC; diferença registrada, sem descarte. P164/2248 preservado como uma oferta com teoria41 e práticas21+20; 2248/manhã separado de2348/noite e2287/noite. Treze linhas em quarentena (11 marcadores não numéricos; 2 PCS107A repetidas), todas preservadas com células/fórmulas/linha/arquivo. Sem ocupação real ou PRIME inventados.

17 testes PASS em Docker tools com PostgreSQL real: contagens, P164, P110A, cursos, eletiva como elegibilidade, reimportação sem duplicação e rejeição de payload divergente com rollback. Evidências artifacts/reports/v4/import-report.json, source-mapping.csv, academic-import-junit.xml. Runbook e contrato academic_reference_v4.md atualizados. Fontes XLSM originais não alteradas. Sem reset/rebuild dos serviços principais.

FaseA ainda parcial: staging com chaves canônicas e proveniência implementado; normalização completa de dimensões/fatos pendente. FasesB-F ainda não executadas. PDFs funcional/arquitetura e diagnóstico seguem SOURCE_MISSING; localização solicitada ao usuário. Continuar V4 sem declarar concluída nem atribuir PASS ao E2E. Preparar checkpoint local conforme SPEC, sem push.

# 05/11/2026 — V4 iniciada; fontes acadêmicas ausentes

SPEC V4 lida. Fontes obrigatórias não encontradas no repositório (incluindo busca de arquivos ignorados em data/dev/docs/reference). Pergunta enviada ao usuário sobre localização do pacote reference, ainda sem resposta. Gate A bloqueado: não inventar 107 registros nem simular estrutura acadêmica por números citados. Fluxo existente preservado; nenhum serviço ou banco alterado.

Implementado inventário de fontes somente leitura com SHA256, SOURCE_MISSING/AMBIGUOUS e exit code 2. Catálogo independente de métricas 1.0: oito métricas, seleção validada, NOT_EVALUATED com motivo e consolidação por observações comparáveis. 12 testes PASS em container isolado sem rede, artifacts/reports/v4/foundations-junit.xml. Validação estática e lint PASS. Integração acadêmica/Workbench/MLflow e simulador09 V4 ainda pendentes; matriz de 25 critérios NOT_EXECUTED, manual MANUAL_NOT_CHECKED. Não declarar V4 concluída. Runbook documenta comandos e gates. SPEC autoriza checkpoints pequenos por fase; preparar commits locais, sem push nesta etapa.

# 05/11/2026 — continuidade automática 01 → 02 aplicada

Pedido: remover a cópia manual de ID entre a jornada e a conferência de inferência. Notebook01 agora salva atomicamente /workspace/reports/journey-current.json depois das evidências concluídas; notebook02 usa esse contexto, com prioridade para ID manual. Compatibilidade com /reports/journey-latest.json existente. Confere ciclo, execution_id, run_id, snapshot, nome e versão na API; não procura a última proposta/modelo no banco, não gera proposta automaticamente. Contexto ausente, inválido ou divergente pede seleção explícita.

Imagem Jupyter reconstruída e container saudável; fontes distribuídas ao workspace com preservação das cópias anteriores fora da lista ativa. Sete testes PASS (artifacts/reports/v3/continuation-junit.xml). Notebook02 editável executado inteiro em kernel novo sem PROPOSAL_ID: PASS, API/SQL/storage reconciliados; artifacts/reports/v3/continuation-auto-check.executed.ipynb e relatório JSON/Markdown. Escrita de contexto novo da jornada01 coberta em teste; não executado novo treinamento nesta correção. Dados e evidências anteriores preservados. Usuário autorizou commit e publicação desta correção na development. Incluir código, notebooks, documentação e evidências continuation; relatórios de outros testes locais ficam preservados fora deste commit.

Publicação anterior confirmada: efc87b5 enviado à development do GitHub Quanticoi/marista-horas-intel-poc-ia em 04/11.

# V3 — código finalizado para teste local pelo usuário

Pedido posterior: commit autorizado pelo usuário na branch development. Incluir implementação, documentação e evidências V3; push e PR não solicitados nesta etapa. Validação estática, lint e verificação de segredos passaram antes do commit.

Orientação mais recente: finalizar o código e deixar o teste local com o usuário. Não prosseguir com automação visual nem exigir CI remoto para esta entrega. Implementação e imagens aplicadas; 85 testes principais passaram. Nenhum ajuste funcional identificado permanece pendente. Não criar commit/PR sem pedido explícito.

Entrega: artifacts/reports/v3/acceptance-v3.md/json, estado READY_FOR_LOCAL_TEST. Conferência local ficou com o usuário; resultados não executados continuam identificados, sem falsa aprovação manual. Histórico e evidências preservados.

## Estado anterior — mantido como histórico

# V3 em implementação — 04/11/2026

Base b02739c, diagrama startup preservado. V3 implementada e rebuild principal aplicado com migration008 aditiva. Suíte principal: 85 testes, zero falhas/erros (artifacts/reports/v3/main-suite-junit.xml). Preservação comprovada de 83 runs, 57 versões, 22 propostas e 395 objetos; notebooks anteriores preservados. Dez notebooks executados em kernels novos na stack isolada; três modelos distintos, duas versões, geração API e recuperação sem Jupyter comprovados. Reset-data/empty e factory-reset/demo-ready PASS somente no projeto isolado. Nenhum reset principal.

Revisão final aplicada: assinatura validada antes de desserializar, cache sincronizado, auditoria verifica manifesto da proposta e atribuição de linhas, snapshot SQL/S3 e tags removidas de ambos os objetos. Imagens atualizadas; 85 testes principais novamente PASS. Dez notebooks isolados em kernels novos PASS, negativos ampliados PASS e recuperação de três modelos sem Jupyter novamente PASS. Workspace principal: dez notebooks editáveis e gravação/releitura pela API PASS; notebook04 executado com chave funcional DEMO. Relatórios novos em v3, sem reaproveitar v2 como destino.

Matriz consolidada em artifacts/reports/v3/acceptance-v3.md/json: 17 AUTO_PASS, 2 MANUAL_NOT_CHECKED e 1 BLOCKED (CI remoto). Pendentes: conferência visual completa e CI remoto em checkout limpo. Computer Use encerrou a tentativa anterior por não conseguir determinar a URL do navegador com segurança; UI permanece MANUAL_NOT_CHECKED até observação real. Não criar commit/PR nesta etapa, conforme spec V3. Alterações ainda não publicadas. Evidências e índice SHA em artifacts/reports/v3.

# Estado atual — V2 validada e repositório revisado

04/11/2026. Onze serviços principais saudáveis em Docker Compose. Código final
798b586; CI41903976793 aprovado com instalação limpa, 79 testes e notebooks
com escrita explícita. Matriz técnica 16/16 em artifacts/reports/v2/acceptance-v2.md.

Jornada 01 executada no workspace em kernel novo: modelo 15, run
c0d9f3138c874049b339e0f54ab8348c, execução 712b11cd-a96a-4bb9-83bb-691724ceae88.
Foram lidos 1.050 registros SQL e reconciliadas 90 linhas de proposta pela API.
Geração operacional pela API/worker:6391c652-a079-4a73-a6c6-a385e8b9774f.

Campanha isolada 417cb008-faac-4cfe-9220-94d16bbf421a: 500 treinos reais em 310,72 s,
concorrência 2. Snapshot DEMO compartilhado; isso não comprova qualidade acadêmica
real ou 500 modelos carregados simultaneamente. Serving: 60 chamadas com 6 versões,
p95 aproximado 0,383 s. Pausa, retomada, cancelamento, falhas MLflow/SQL,
SIGKILL do worker com retomada de 30 treinos sem duplicação, aprovação, revogação,
rollback, hashes e lineage N:N passaram. Ambos os resets e as jornadas posteriores
passaram exclusivamente na stack isolada; seus containers agora estão parados.

O ambiente principal preservou 69 runs concluídas, 49 versões e 12 propostas anteriores.
Arquivos anteriores conferidos por hash; templates antigos e edições preservados
fora da lista do Jupyter. Nenhum backup de banco novo e nenhum reset principal.
Dez notebooks editáveis, com uma única jornada principal. Escrita e releitura pela
API do Jupyter comprovadas após o último rebuild.

Revisão em docs/REPOSITORY_REVIEW.md: dez scripts obsoletos e 33 imports sem uso
removidos. Dev contém apenas README e três especificações. Ferramentas recorrentes
em deployment/scripts; ensaios em tests/acceptance, ambos com índices de uso.
Cache antigo de dev removido. Geração de credenciais unificada; gravação atômica
para relatórios compartilhados; corrigidas correlação dos logs, paginação do
grafo e busca paginada de versões para recuperação.

Sem pendências de implementação ou aceite técnico V2. Dados reais e homologação
acadêmica permanecem fora do aceite DEMO; contrato provisório identificado.
Somente development publicada; staging e main sem merge.

## Histórico de estados anteriores (não é orientação atual)

# Estado atual - revisão V2 em validação final

04/11/2026: usuário acrescentou code review completo e limpeza. Dez scripts V1/diagnósticos obsoletos removidos com hashes em artifacts/reports/v2/repository-cleanup.json. Imports sem uso removidos; corrigidos correlação da inferência, paginação de edges, recuperação paginada do Registry, inventário do notebook09 e quiescência do reset. Credenciais unificadas no inicializador Python; Dockerfiles reorganizados para cache. Reset-data/empty e factory/demo-ready PASS somente isolado, seguidos das jornadas A/B. SIGKILL do worker recuperou campanha30 sem duplicar versões. Principal preservou69runs/49versões/12propostas; jornada v14 PASS. Nenhum backup de banco novo. CI4b6314b PASS; código da revisão ainda em validação.

## Histórico de estados anteriores (não é orientação atual)

# Atualização — 04/11/2026: correções v1.1 validadas

V2 checkpoint: API/worker de geração, campanhas, revisão, lineage e catálogo
implementados e testados na stack isolada. 500 treinos reais e campanha30 PASS;
72 testes gerais e6 testes finais de operações/traces PASS. Todos00–09 e opt-in
02/04/05/07 executados; repetição04 mesma chave não duplicou versão. Negativos de
checksum/artefato ausente/mapping, rollback SQL, governança/revogação/rollback e
reparo de manifest PASS. Pause/resume/cancel, MLflow indisponível+retry e SQL503
PASS. Serving60chamadas/6versões/concorrência2 p95~0.52s p99~0.70s. Evidências
isoladas em artifacts/reports/v2/isolated. Falha real de tempestade de mensagens
foi corrigida com claim de envio persistente (migration007); perda do observador
HTTP não perdeu jobs. Restam resets/rebootstrap isolados, deploy principal com
preservação, CI e relatório final. Nenhum reset principal e nenhum backup novo.

V2 EM IMPLEMENTAÇÃO conforme dev/spec_correcoes.v2.md. Inventário antes em
artifacts/reports/v2/inventory-before.json, HEAD9306f14. Usuário dispensou backup
de banco na fase atual de montagem; prosseguir sem esse gate. Preservar dados
principais e executar qualquer reset somente na stack isolada. Migration006,
jobs persistentes/campanhas/API de geração/governança estão em desenvolvimento,
ainda não validados. Links MLflow corrigidos e jornada consolidada em um único
01_jornada_completa_planilha_turmas.ipynb; cópias exatas em notebook-backups.
Dez notebooks do catálogo V1.1 executados do workspace em kernels novos PASS;
escritas opt-in ainda pendentes de implementação/aceite V2. Última jornada v13,
execution81d0a4af-b0d4-4a3f-b99e-671159d59fed, 90linhas SQL/API.

Resultado atual: artifacts/reports/correcoes-v1.1-acceptance.md e JSON associado.
Docker principal atualizado: 59 testes, 19 verificações HTTP e notebooks em
kernels novos PASS. Execução 8d373b5a-f73d-4daa-b5cb-cde6ac238087, modelo v11,
run 6d3153d23589442b8475e969f82a1d98; 1050 registros SQL e 90 linhas de proposta.
CI remoto 41847743558 aprovado no commit feebce9, incluindo instalação limpa.
Volumes, modelo v8 e proposta anterior preservados após rebuild, com hashes
conferidos. Notebook original preservado; abrir a cópia atualizada editável
01_jornada_completa_planilha_turmas.update-eeacc6e47d5c.ipynb no Jupyter.
Catálogo auxiliar: nove notebooks PASS. Reset preview principal sem alterações;
factory-reset e reset-data comprovados exclusivamente na stack isolada, agora
parada. Nenhum reset no projeto marista. Evidências incluem prova independente
SQL/SDK/S3/API após reset isolado. Scheduler persistente de campanhas permanece
NOT_IMPLEMENTED; benchmark mediu 30 treinos reais e 500 identidades, não 500
treinos. Contrato técnico DEMO não homologa regras acadêmicas V4.4.
Último ajuste PowerShell mantém PROPOSAL_ID opcional vazio no bootstrap; parser
validado. Os registros abaixo documentam os estados anteriores da execução.

04/11/2026 — aceite parcial v1.1: migration005 e imagens aplicadas no projeto
marista, volumes preservados. Jornada01 e notebook02 PASS no ambiente principal:
execution93519267-7809-4e64-9e04-a79b9fb03d40, run69fdee4b8f744f88b03117dfa2eaa5bb,
planilha-turmas-demo v10,1050 SQL/90 propostas. Suíte58PASS;10 jornadaPASS.
Workspace01 original preservado byte a byte (AB37343F...); nova versão distribuída
como 01_jornada_completa_planilha_turmas.update-eeacc6e47d5c.ipynb.
Stack isolada: notebook01/02 PASS,35unit+17integração PASS;30 treinos reais11s,
500 identidades0.34s (não500treinos); proposta N:N duas versões/90linhas PASS.
Factory-reset isolado plano8479badb-3529-4e07-b94f-88355fe8a25a RESET_PASS:
demo-ready,zero runs/propostas,arquivos protegidos preservados.6guardasresetPASS.
Pendente nesta atualização: smoke catálogo, prova pós-rebuild, reset-data isolado,
relatório consolidado e CI remoto. Scheduler persistente de campanhas está
explicitamente NOT_IMPLEMENTED (evolução incremental permitida pela spec).

04/11/2026 — spec-correcoes v1.1 EM IMPLEMENTAÇÃO. Diagnóstico em
artifacts/reports/correcoes-fase-a-2026-11-04.md. V3 e V4.4 localizados e consultados
no Drive. Módulo HI-LINEAGE, migration005 aditiva, contrato application-view,
lookup lineage e notebook02 em desenvolvimento; ainda não aceitos ponta a ponta.
Stack separada marista-correcoes-isolated criada após esgotamento do pool padrão
de redes Docker, com subnet livre 10.254.241.0/24. Nenhuma rede alheia removida.
Causa CI reproduzida: mlflow db upgrade em banco vazio falha UndefinedTable metrics.
Inicialização pelo SDK público MLflow antes do upgrade corrigiu banco novo;
MLflow isolado healthy. Não alterados dados/volumes/workspace da stack marista.

04/11/2026: dev/spec.md renomeado para dev/spec-historica-v1.md por solicitação
do usuário, com aviso explícito de documento histórico. Validador SQL e ADR-002
ajustados; contrato SQL original preservado. spec.md da raiz continua a referência
principal, sujeita às decisões atuais registradas aqui. Arquivo local não versionado
dev/spec-correcoes.md encontrado e preservado sem alterações.

04/11/2026: acesso RustFS destacado no início do README e em seção própria:
console localhost:9001, campos de login relacionados às chaves do .env, bucket
pucpr-poc/prefixo mlflow e diferença entre portas 9001/9000. Alteração documental;
sem modificar credenciais nem reiniciar serviços. Validação estática PASS.

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
