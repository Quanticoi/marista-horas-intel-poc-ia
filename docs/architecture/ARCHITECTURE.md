# Arquitetura V4

O runtime é `compose.yaml`, com onze serviços contínuos e duas imagens próprias:
aplicação Python e Jupyter. PostgreSQL, RustFS e RabbitMQ usam imagens específicas.
O [diagrama de componentes](../../README.md#arquitetura) apresenta o fluxo principal.

| Componente | Responsabilidade vigente | Persistência |
|---|---|---|
| Jupyter / Workbench | Leitura SQL, preparação, fit, avaliação e campanhas locais | Checkpoints em PostgreSQL; runs no MLflow |
| MLflow 3.11.1 | Tracking, Tracing, Registry e proxy de artefatos | `mlflow_db`; binários no RustFS |
| API | Contratos HTTP, governança, deploy e solicitação de geração | Jobs e auditoria em PostgreSQL |
| Worker / RabbitMQ | Orquestração recuperável da inferência e composição de propostas | PostgreSQL é a fonte de verdade; RabbitMQ transporta tarefas |
| Inferência | Versão aprovada, integridade do binário, PRELOAD/LAZY e predict | Cache de até quatro versões por processo; evidência em manifests |
| PostgreSQL 15.10 | Fonte acadêmica, simulação e dados de negócio | Volume nomeado; bancos lógicos separados |
| RustFS 1.0.0 | Objetos S3 e versionamento | Volume nomeado; bucket `pucpr-poc` |
| Dashboard / monitoramento | Eventos correlacionados e saúde | JSONL em `data/compose-logs`; consultas de estado |
| Ingestion | Compatibilidade com entrada agregada anterior | Não é o importador da jornada V4 |

## Fronteiras de execução

O fit roda no container Jupyter, com `WORKBENCH_EXECUTOR=1`. O worker recusa jobs
de treinamento; rotas antigas de submissão de treino retornam 410. A proposta
é composta pelo worker, a partir de chamadas HTTP ao serviço de inferência.
Notebook 09 consulta a API exclusivamente por HTTP; não abre SQL nem treina.

Não há um novo container por modelo no fluxo V4. Aprovação técnica cria autoridade
SQL e alias `champion`; deploy registra política e validade. PRELOAD carrega no
startup, LAZY carrega na primeira chamada. Registro, aprovação e residência em
memória têm estados diferentes. A elegibilidade é conferida também no cache quente.

## Bancos e artefatos

Uma instância PostgreSQL hospeda `planejamento_db` e `mlflow_db`. O schema
`planejamento_db.planning` contém fontes, simulação, campanhas, aprovações e propostas.
O papel `planning_readonly` lê a fonte; `planning_app` grava dados operacionais;
`planning_migration` aplica migrations. O MLflow administra seu próprio schema e
executa `mlflow db upgrade` antes de liberar HTTP. A aplicação não escreve nele.

O SDK envia o modelo ao proxy MLflow; somente o servidor grava seus binários no
prefixo `mlflow/` do RustFS. Manifests de lineage referenciam os bytes e hashes,
sem duplicar o modelo. PostgreSQL, RustFS e RabbitMQ têm volumes persistentes;
workspace e relatórios são diretórios montados do projeto.

## Rede e inicialização

Entre containers: `postgres`, `mlflow`, `api`, `inference`, `rustfs` e `rabbitmq`.
No navegador: portas em loopback, listadas em [Acessos](../operations/ACESSOS.md).
Bootstrap cria dependências, aplica migrations e aguarda healthchecks; não treina.
O notebook 00 acrescenta operação real de tracking e gravação/leitura de artefato.

O [mapa C3](../operations/C3_TRAINING.md) demonstra responsabilidades funcionais.
Esta execução local não comprova implantação, segurança ou capacidade em nuvem.
