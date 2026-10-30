# ADR-006 — Separar execução de modelos e manter pod de monitoramento

Solicitação explícita do usuário: mlops deve ter MLflow e monitoramento; ai-service
deve ter modelos de inferência e API de Serviços Inteligentes, com scripts disponíveis.

Substituir o CronJob suspenso por Deployment `monitoramento`, polling readonly a cada
30 segundos, probes e token próprio. Não cria treinos nem aprova versões.

Separar `inference` de `api`. API/worker mantêm orquestração e persistência; executam
previsões por HTTP interno autenticado. Inference valida deployment aprovado e alias,
carrega JSON somente do bucket/prefixo autorizado no RustFS, verifica schema/snapshot,
mantém cache limitado por versão e retorna proveniência. Sem fallback local na API
caso inference esteja indisponível. S3 fica fora dos Secrets da API/worker.

Uma réplica inicial atende os 30 modelos. Worker separado preserva processamento
assíncrono via RabbitMQ. O fluxo local de namespaces foi substituído pelo Compose
na ADR 007; scripts/guia específicos do Rancher foram removidos na revisão de legado.
Nenhuma coluna ou migration muda nesta revisão de topologia.
