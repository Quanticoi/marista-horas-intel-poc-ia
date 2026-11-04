# Organização e capacidade de modelos

V3: novos escopos DEMO usam `hi.pt.demanda.DEMO-C1.DEMO-CR1.P1`, derivado do
catálogo SQL. Treino é filtrado por período antes do split; default da campanha
no notebook05 é três escopos. Experimento fixo por domínio/ciclo e nomes de run
incluem algoritmo/UTC/tentativa. Consulte o [dicionário](../contracts/HI_TAGGING_STANDARD.md).
Os 500 ensaios V2 tinham um SHA distinto de model.pkl: constituem teste de
orquestração, não 500 comportamentos acadêmicos nem aceite do código V3.

Um MLflow por ambiente; experimento por domínio/campanha; run por tentativa;
Registry por identidade estável. Nomes legados planilha-turmas-demo e C1-CR1-P1
não são renomeados. Novos ensaios usam hi.demo.*; tags incluem solução, ambiente,
domínio, ciclo, snapshot, campanha, model_key, código, configuração e hashes.

Notebook05 agora submete campanhas persistentes pela API. PostgreSQL armazena
training_campaigns, operation_jobs e operation_events; a view training_campaign_items
expõe run/versão/métricas. RabbitMQ/Celery transporta tarefas; dispatcher10s,
claim de envio60s, heartbeat10s e advisory locks controlam duplicidade/recuperação.
Paralelismo máximo2; retries1–4, backoff10–60s; cancelamento cooperativo. Estado
FAILED é sinalização persistente, não uma mensagem perdida.

V2 executou campanhas de30 e500 treinamentos reais com fit, métricas, Registry e
três arquivos comparados no storage por item. Os modelos são identidades sintéticas
distintas treinadas sobre o mesmo snapshot agregado. Não representam500 cursos
reais nem prova de qualidade institucional. Relatórios de campanha distinguem
contagem, CPU, RSS de processo, timestamps e observação após retomada.

T5 usa seis versões da campanha500, sessenta chamadas, concorrência2 e reinício
prévio do serviço. Reporta p50/p95/p99 e estatísticas do cache. Não equivale a500
modelos simultâneos. Cache LRU comporta até4 versões por processo, só após conferir
SHA antes de desserializar. Registro não carrega modelo nem provisiona API.

Serving compartilhado é a opção medida desta POC. Serviço dedicado continua no
fluxo legado quando explicitamente publicado. Decisão de produção exige SLO,
isolamento, tamanho de binário, concorrência e pressão de memória medidos.

Governança V2: solicitação/revisão em model_approval_requests, credencial de
operador separada e alias champion concordante; registro não aprova. Serving
legado mantém model_deployments/bundle2.0. [ADR010](../adr/010-durable-operations-v2.md).
