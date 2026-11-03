# Experimentos, repetição, Traces e persistência

## O que acontece ao repetir uma célula

Jupyter executa seu conteúdo novamente e substitui as variáveis atribuídas. Ele
não fornece deduplicação automática. Não se deve confundir repetir uma leitura
com iniciar outro treinamento.

| Etapa | Ao executar novamente |
|---|---|
| Configuração inicial | Gera outro execution_id; começa outra jornada. Não executar no meio de uma run ativa. |
| SQL/preparação | Reconsulta/recalcula; o snapshot e hash identificam os dados. |
| Instanciar modelo | Cria um estimador ainda não treinado. |
| Abrir tracking | Abre uma run; não é uma operação de retomada automática. |
| Treinar | Executa fit/predict novamente; exige a run correspondente ativa. Métricas têm histórico. |
| Registrar | Com trace/model_version já preenchidos, valida e reutiliza a versão desta execução. Não retreina nem publica outra versão. |
| Inferir | Recarrega a versão explícita e executa novamente; não treina. |
| Compor | Recalcula as linhas usando a regra/capacidade. |
| Persistir | Mesmo execution_id e conteúdo: retorna o registro existente. Conteúdo diferente: rejeita; não sobrescreve. |
| Conferir SQL/Storage/API | Somente leitura. |

Restart Kernel and Run All cria nova execução, nova run/versão e nova geração da
proposta. Para retomar após reiniciar o kernel, os identificadores devem ser lidos
de um relatório salvo e o modelo carregado por versão; variáveis anteriores não
existem mais. Retomada automática de qualquer célula ainda não está implementada.
O registro repetível não é uma transação distribuída: falha entre upload e retorno
do Registry requer reconciliar a run antes de tentar registrar novamente.

## Definir o experimento

Configure no `.env` local, sem credenciais:

```dotenv
MLFLOW_EXPERIMENT_NAME=planilha-turmas-proxy-v1
```

O Compose propaga o mesmo nome a Jupyter, API e inferência. Após mudar, execute
`deployment/scripts/compose.ps1 start` para recriar os serviços afetados e inicie
um kernel novo. O notebook cria/recupera o experimento e mostra seu nome/ID.
Mudar o experimento não muda o modelo registrado nem apaga runs anteriores.
`MODEL_NAME` é outro conceito: nome estável no Registry, atualmente
`planilha-turmas-demo` na jornada DEMO.

Um experimento reúne treinamentos comparáveis pelo objetivo, alvo, contrato de
dados e métricas. Exemplo futuro: `marista/demanda-turmas/demo/v1`. Ciclo, curso,
coorte, snapshot e algoritmo devem ser tags/params, evitando uma lista de
experimentos para cada data ou tentativa.

## Tracing implementado

Cada chamada a step após validar dependências abre um trace independente, com
stage, attempt e execution_id. A duração mede aquela tentativa da etapa, não o
tempo em que o usuário deixou o notebook aberto. Etapas falhas ficam em ERROR.
O resumo final associa os traces a run/modelo/versão e exibe links. Em caso de
falha anterior ao resumo, pesquise a tag execution_id na aba Traces.

Inferência e consulta de propostas propagam contexto W3C nos headers HTTP. Seus
spans remotos aparecem no trace da etapa chamadora, com carga/predição do modelo
e consulta SQL. Não capturamos corpos HTTP, tokens, URLs SQL, amostras acadêmicas
nem mensagens brutas de exceções. Apenas metadados técnicos permitidos.
Checagens de saúde e navegação comum sem contexto não geram traces.

Runs continuam registrando experimentação; traces mostram execução. O dicionário
`trace` do notebook contém referências do Registry; `trace_id` é o ID do Tracing.
Documentação: [propagação entre serviços](https://mlflow.org/docs/latest/genai/tracing/app-instrumentation/distributed-tracing/).

## Conferir o modelo no Object Store

A etapa 7b lê a versão exata no Registry, baixa seus arquivos pelo proxy e lê os
mesmos objetos diretamente no RustFS. Compara SHA256 de `model.pkl`, `MLmodel` e
`requirements.txt`, exibindo bucket, chave, tamanho e hash. Não grava outra cópia
no bucket. O recarregamento seguinte comprova que o binário também é utilizável.
Console: http://localhost:9001; bucket `pucpr-poc`, prefixo `mlflow/`.
Esta checagem direta usa as credenciais S3 já disponíveis no Jupyter somente para
leitura de evidência; a gravação do modelo continua exclusivamente pelo MLflow.

## Conferir a proposta no banco de negócio

Banco `planejamento_db`, schema `planning`:

- `proposal_generations`: cabeçalho, status, snapshot, run, modelo, versão e regra.
- `proposal_lines`: disciplina/curso/período, previsão bruta, alunos/turmas propostos
  e ajuste humano (nulo na demonstração).

A etapa 10b abre uma conexão nova após o commit e compara **todas** as linhas com
a proposta gerada. A consulta parametrizada está em
[verify_proposal.sql](../../sql/queries/verify_proposal.sql). Para conferir em um
cliente SQL, substitua `:execution_id` por um parâmetro UUID da execução mostrada
no notebook. A etapa 11 consulta `/v1/proposals/{execution_id}` e `/lines`, e
reconcilia os mesmos valores. Isso é separado do banco `mlflow_db`.

## Organização para mais de 500 modelos

Primeiro defina o grão funcional: 500 modelos independentes não são 500 versões
do mesmo modelo, nem necessariamente 500 experimentos. Reutilize o catálogo
`planning.model_catalog`, sua model_key e mlflow_registered_name.

| Objeto | Convenção proposta para a evolução |
|---|---|
| Experimento | Família/objetivo + ambiente + versão do contrato. Poucos experimentos. |
| Campanha | Uma run pai por lote/ciclo, identificada por campaign_id. |
| Treinamento | Uma run filha por model_key e tentativa; falha/retry independente. |
| Tags | campaign_id, model_key, ciclo, curso/coorte, snapshot_id, code_version, modo. |
| Registry | Um nome estável por modelo independente; versões sucessivas para retreinos. |
| Seleção | Versão explícita; alias champion somente após aprovação e auditoria. |

Exemplo de nome futuro, após pactuar o grão: `demanda-cr001-coorte01`. O ciclo
pertence à campanha/versão, não precisa fazer parte do nome estável do modelo.
O fluxo legado já treina por model_key e registra modelos separados. A jornada
principal permanece com um modelo DEMO; **500 modelos, campanhas pai/filhas e
carga concorrente não foram implementados ou testados nesta alteração**.

Para executar em escala: despachar tarefas pelo RabbitMQ/Celery existente,
limitar concorrência à memória/CPU disponíveis, usar chave de trabalho composta
por campanha/model_key/snapshot/configuração, e persistir progresso no PostgreSQL.
Uma falha não deve repetir os 499 modelos já concluídos. MLflow organiza os
resultados; não substitui o agendador nem implementa essa idempotência sozinho.
Não criar automaticamente um container por modelo: o serviço existente pode
carregar versões sob demanda, com cache limitado. A proposta consolidada precisa
registrar a versão usada por modelo e validar a completude do lote antes de publicar.
Esse vínculo exige uma evolução própria do schema atual, que hoje referencia um
modelo por geração; não está sendo apresentado como já entregue.

Referências: [Tracking e runs filhas](https://mlflow.org/docs/latest/tracking/),
[Registry e aliases](https://mlflow.org/docs/latest/ml/model-registry).
