# MLflow V4

Servidor e SDK usam **3.11.1**. Tracking, Registry e Tracing persistem em
`mlflow_db`; artefatos passam pelo proxy MLflow e ficam no RustFS. O servidor
executa a atualização oficial do schema antes de aceitar tráfego. Não há SQLite
ou fallback de tracking local na jornada.

Uma nova campanha cria seu próprio experimento. Modelos mantêm nomes estáveis por
curso e versões distintas. Retomar campanha é ação explícita. A run diagnóstica
confere metadados e gravação/leitura real de artefato antes de fit.

- [Abrir MLflow](http://localhost:5000).
- [Passo a passo na interface](MLFLOW_TUTORIAL.md).
- [Campanhas, repetição e Traces](EXPERIMENTS_AND_TRACING.md).
- [Reset de experimentos](RESET_POC.md).

O modo proxy envia os bytes uma única vez pelo SDK. O notebook e o auditor podem
ler o objeto para verificar SHA256; isso não é uma segunda persistência do modelo.
MLflow fica acessível por loopback nesta POC. Senha de PostgreSQL não é login da UI.
