# Diagnóstico da evolução v1.1

Base: development, ef28bda9d47e9d57878d193507e968f41cb95ff0. Inspeção em 04/11/2026.
Os onze serviços Compose estão healthy no ambiente existente. Nenhum reset realizado.

| Existente | Ajuste | Cobertura funcional |
|---|---|---|
| Jornada SQL/Ridge/Registry/proxy/S3/SQL/API real | Preservar e acrescentar identidade tipada | RF157 parcial, DEMO |
| proposal_generations e proposal_lines, migration004 | Tabelas relacionadas aditivas; execution_id permanece alias da proposta | RF204 original preservado |
| Uma versão por cabeçalho legado | Relação N:N e grafo, sem reescrever cabeçalho | RGN002 não homologada |
| Respostas SQL cruas autenticadas | application-view versionado e lineage paginados | RF008/009 parcial |
| Capacidade 40 e previsão de total | Identificar regra POC; componentes desconhecidos nulos | RF021–025, RF040–047 não avaliados |
| Notebook01 editável | Catálogo00–09 e distribuição sem sobrescrever edições | Operação técnica |
| Traces por tentativa e provas de bytes | Propagar IDs independentes e manifests imutáveis | RF195–199 parcial |
| CI falha antes do notebook | Diagnóstico antes da limpeza, reprodução isolada | AC14 pendente |

PostgreSQL: planejamento_db/planning contém negócio e metadados operacionais;
mlflow_db é administrado exclusivamente pelo MLflow. RustFS: pucpr-poc,
mlflow/ controlado pelo MLflow, snapshots existentes preservados. DNS internos
postgres, rustfs, mlflow, api, inference. Endereços de navegador no README.

Referências consultadas no Google Drive (somente leitura):
- [Componentes V3](https://drive.google.com/file/d/1mdGx9bwyUekmJL3ZmAhFugslgYgWQ_Nh/view)
- [Containers V3](https://drive.google.com/file/d/1jYDmgi5kvUxcWMqJWhbs1ztG9yONDzUY/view)
- [Sequência V3](https://drive.google.com/file/d/1QdiJeaRGaPnQT1rX0-h-qZvQm7FfPxvi/view)
- [Requisitos V4.4](https://drive.google.com/file/d/1R6Af10isKrkju_JcwN1UVh-5lwvCAl1h/view)

V3 atribui persistência/orquestração operacional ao worker da aplicação. A escrita
DEMO atual pelo Jupyter é um adaptador demonstrativo, não decisão de arquitetura
definitiva. V4.4 exige validação humana da matriz antes de docentes/turmas especiais;
modulação institucional depende da matriz e unificação. Não há dados suficientes
para homologar essas regras. Dados sintéticos não são integração PRIME.

CI 41830130011: unhealthy cerca de 16s após startup; logs internos não foram
coletados pelo workflow. Isso não prova timeout nem erro de credencial. Causa ainda
em investigação; nenhuma alteração de probes justificada apenas por esse sintoma.
