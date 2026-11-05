> **Registro de decisão anterior.** A jornada V4 é regida pela [ADR 012](012-workbench-academic-v4.md). Topologias, comandos ou responsabilidades deste registro podem ter sido substituídos; use a [documentação operacional atual](../README.md).

# ADR009 — Identidade e contrato de proposta

Data04/11/2026. Estado: decisão técnica POC, contrato funcional pendente de homologação.

Preservar execution_id como alias de proposal_id e cabeçalho legado. Acrescentar
relações N:N, grafo e evidência imutável pela migration005. Backfill parcial deixa
campos desconhecidos nulos. Não reproduzir schema MLflow nem usar FK entre bancos.

Contrato poc-planilha-turmas-v1 é gerado por adaptador Pydantic independente do
notebook, com endpoint HTTP autenticado e hash canônico por página. Revisão1
representa o original; revisão humana requer contrato futuro, sem overwrite.
Modulação40, composição de estudantes e coortes não são decisões funcionais.

Manifests auxiliares são imutáveis e publicados após commit SQL; retry permite
recuperar falha de publicação. Artefatos do modelo têm uma única escrita pelo
proxy MLflow. Versão explícita para DEMO não implica aprovação operacional.

V3 coloca orquestração/persistência de negócio no worker da aplicação. A escrita
Jupyter permanece adaptador POC; transferência de responsabilidade exige alinhamento.
[Metodologia](../architecture/LINEAGE.md) e [contrato](../contracts/README.md).
