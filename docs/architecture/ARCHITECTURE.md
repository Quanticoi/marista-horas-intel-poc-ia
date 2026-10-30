# Arquitetura atual

Onze serviços Compose, dois utilitários e uma API adicional por modelo publicado.
Jupyter representa o Workbench e não recebe credenciais PostgreSQL: usa SDK/HTTP/S3.

```mermaid
flowchart LR
  J[Jupyter / SDK] -->|dados e estado do treino HTTP| D[Entrada de dados]
  J -->|tracking e registry HTTP| M[MLflow]
  J -->|upload direto de binários S3| S[RustFS]
  D --> P[(PostgreSQL planejamento_db / planning)]
  D --> S
  M --> Q[(PostgreSQL mlflow_db / public)]
  A[API de negócio / Celery] --> R[Roteador inference]
  A --> P
  R --> I[API exclusiva por modelo aprovado]
  I -->|alias e versão| M
  I -->|binário verificado| S
  I -->|aprovação e proveniência| P
```

Volumes nomeados preservam PostgreSQL/RustFS/RabbitMQ; Jupyter monta workspace/.
Dashboard mantém dados de negócio e histórico de logs. Logs atuais via Compose.
Collector Kubernetes permanece reservado à referência Helm.
API faz previsão síncrona; batch usa RabbitMQ/Celery com estado durável no banco.
P e Q são bancos distintos da mesma instância PostgreSQL; SQLite não é usado.
Cada API dedicada carrega um binário aprovado e nunca treina durante a previsão.
Registro, aprovação e publicação são etapas separadas. Publicação ocorre pelo host/pipeline,
sem Docker socket nos containers. Monitor não dispara treinamento.
MLflow usa psycopg2; aplicação usa psycopg3.
[Operação C3](../operations/C3_TRAINING.md). [Kubernetes futuro](../../deployment/helm/README.md)
é referência histórica; ainda não inclui estes novos serviços nem uma implantação GCP validada.
