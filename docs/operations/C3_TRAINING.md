# Correspondência entre a jornada V4 e o C3

| Responsabilidade C3 | Implementação local | Etapa / evidência |
|---|---|---|
| Workbench científico | Jupyter, módulos `src/workbench/academic_*` | 00–06; fit/predict real e campanhas locais |
| Fonte de dados | PostgreSQL, referências e histórico sintético versionado | 01–03; SQL, hashes, quarentena |
| Tracking e registro | MLflow com PostgreSQL e proxy S3 | 04–06; experimento, runs e versões |
| Object Store | RustFS | Binários sob gestão MLflow e manifests de lineage |
| Governança de modelo | API, SQL e alias Registry | 07; revisão técnica explícita |
| Serving | Serviço `inference`, PRELOAD/LAZY | 08; bytes persistidos, versão elegível e predict |
| Processamento operacional | API → RabbitMQ → worker | 08; job, inferência e transação da proposta |
| Aplicação consumidora | API e notebook 09 exclusivamente HTTP | Tabela paginada e filtros acadêmicos |
| Auditoria/observabilidade | Notebook 10, Traces e dashboard | Correlação entre proposta, inferência e modelos |

Treinamento não ocorre no worker operacional. A geração não exige Jupyter aberto
depois que as versões estão aprovadas e disponíveis. A implantação usa o serviço
de inferência compartilhado; não cria uma API por modelo na jornada V4.

O C3 é demonstrado por responsabilidades e integrações locais. GCP, PRIME, identidade
institucional, capacidade acadêmica, HA e aprovação funcional não são inferidos.
Use [o runbook](POC_V4_MANUAL_RUNBOOK.md) para executar e
[a arquitetura](../architecture/ARCHITECTURE.md) para consultar fronteiras.
