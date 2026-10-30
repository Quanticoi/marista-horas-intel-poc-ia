# Referência Kubernetes futura

Charts/manifests preservados para staging/produção futuros. Não são necessários
no Compose. Scripts específicos de Rancher local foram removidos.

Antes de usar: publicar imagens imutáveis; configurar storageClass, ingress/TLS,
identidade, limites, backups e pipeline de rollout/rollback.
ConfigMaps devem definir DB_HOST, RABBITMQ_HOST, MLFLOW_TRACKING_URI,
MLFLOW_S3_ENDPOINT_URL, API_URI, INFERENCE_URI, MONITOR_URI e DASHBOARD_URI com DNS
do cluster. Defaults Compose não resolvem serviços entre namespaces.
Secrets devem seguir política institucional. Não é um deploy de produção homologado.

dev/generate_assets.py gera apenas charts/manifests, sem alterar notebooks.
values/local é referência histórica do cluster removido.
