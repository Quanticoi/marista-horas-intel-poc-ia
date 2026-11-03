# C3 local: notebook, binário e API por modelo

Implementação local equivalente: Jupyter/Workbench separado do servidor MLflow;
Tracking e Model Registry no mesmo MLflow; PostgreSQL como único SGBD;
RustFS como armazenamento de objetos. GCP/GKE não são provisionados por este guia.
RabbitMQ é fila de trabalho, não banco de metadados. Não há SQLite neste fluxo.

## Atualizar a instalação existente

Preserve `.env`, volumes e `workspace/`. Na raiz, com Docker Desktop disponível:

```powershell
$env:DOCKER_CONTEXT = "desktop-linux"
.\deployment\scripts\compose.ps1 build
.\deployment\scripts\compose.ps1 migrate
.\deployment\scripts\compose.ps1 start
.\deployment\scripts\compose.ps1 validate
```

O script acrescenta somente `INGESTION_TOKEN` se ausente, sem trocar senhas existentes.
`migrate` aplica as migrations acadêmicas até a revisão atual e o
upgrade do schema MLflow. Faça backup antes de upgrades de versão do MLflow.
Instalação nova continua usando `compose.ps1 init`.

## Base de teste e recebimento

O fluxo complementar por série é acessível pelos módulos de `src.workbench.sdk`, conforme o exemplo abaixo. O notebook distribuído atualmente é a Jornada Completa — Planilha Turmas; os notebooks antigos foram retirados da interface.

Base reproduzível: 350 observações, 30 séries acadêmicas semestrais de 2020 a 2025,
com lacuna temporal e um curso com pouco histórico. Valores exclusivamente sintéticos.
O contrato atual recebe dados agregados por campus/curso/período, não dados pessoais.

O serviço **ingestion**, `http://127.0.0.1:8020/docs`, recebe
`POST /v1/datasets`, protegido por `Authorization: Bearer <INGESTION_TOKEN>`.
O payload de referência é produzido por `src.workbench.sdk.test_dataset()`:

```python
from src.workbench.sdk import connect, test_dataset, submit_dataset, train
connect()
snapshot = submit_dataset(test_dataset())
versions = train(snapshot["id"], model_key="C1-CR1-P1")
versions
```

Para treinar todas as séries use `model_key=None`. Para uma base própria, mantenha
o contrato mostrado no OpenAPI: `source`, `as_of_date`, `target_year`,
`target_semester`, `records`. Não reutilize o gerador de IDs para identificadores
institucionais sem definir o mapeamento de domínio.

Validações: campos e tipos, limites, matrículas não negativas, IDs consistentes,
duplicidades, ordenação por série, corte temporal e limite de 30 séries/10.000 linhas.
Cada série precisa de pelo menos três observações para validação temporal.
O corpo HTTP é limitado a 4 MiB. O hash de conteúdo torna reenvios idempotentes.
Snapshots selados são imutáveis; manifest e Parquet têm checksums conferidos na leitura.
As disciplinas/modulações do cadastro permanecem regras sintéticas da POC.

## Treinamento e persistência

O SDK deste fluxo usa HTTP e S3. O container Jupyter também recebe conexões SQL para a jornada principal de Planilha Turmas.
`MLFLOW_TRACKING_URI` e `INGESTION_URI` precisam ser URLs HTTP(S), sem fallback local.
As credenciais S3 e de entrada vêm do ambiente, preenchidas pelo Compose a partir do `.env`.

- MLflow grava experimentos/runs/parâmetros/métricas/versões no banco `mlflow_db`.
- Entrada de dados grava snapshots e execução de treinamento em `planejamento_db`, schema `planning`.
- O servidor atual usa `--serve-artifacts`. O SDK respeita o destino de artefatos do experimento: a jornada principal usa proxy; experimentos anteriores com URI S3 mantêm acesso direto ao RustFS. O pipeline de bundles deste notebook requer um experimento com URI S3, pois valida os arquivos com `load_bundle`; não reutilize o experimento proxy da Planilha Turmas nesse fluxo.
- O modelo inclui estimador ajustado e lógica de previsão serializada. A inferência nunca chama `fit()`.
- `bundle.json` relaciona SHA256/tamanho de todos os arquivos, run, código, dataset e configuração.
- Antes de registrar uma versão, o treinamento baixa os arquivos, valida hashes e compara a previsão do modelo restaurado.
- `code_version` é o SHA256 de fontes/dependências/configuração. Não depende de Git instalado.

O token do Jupyter não é token MLflow. `MLFLOW_PASSWORD` autentica o servidor no
PostgreSQL. MLflow continua sem autenticação HTTP nesta POC restrita a loopback.
Treinamentos interrompidos podem manter execução RUNNING: encerre o run no MLflow
com status FAILED/KILLED e chame `POST /v1/training/{run_id}/sync` autenticado.
Não force aprovação de uma execução incompleta.

## Aprovar e publicar um servidor por modelo

Revise métricas e use a versão retornada pelo notebook:

```powershell
docker compose run --rm tools promote C1-CR1-P1 VERSAO operador "revisao das metricas"
.\deployment\scripts\compose.ps1 publish -ModelKey C1-CR1-P1
```

A promoção confere arquivos e proveniência, grava aprovação/auditoria no PostgreSQL
e aponta `champion`. Não publica automaticamente. Modelos antigos apenas JSON precisam
ser retreinados; não apagamos os runs/artefatos anteriores.

A publicação gera `.runtime/models.compose.json`, sem valores de segredos, e cria
um container `model-<hash-da-chave>` por modelo. Cada container tem servidor FastAPI,
limite de memória, logs, healthcheck e uma única versão/deployment configurados.
O modelo é carregado na inicialização; readiness falha se foi revogado ou diverge do Registry.
O script exibe a porta local dinâmica de cada API; abra `http://127.0.0.1:PORTA/docs`.
Use `INFERENCE_TOKEN` como Bearer no endpoint `/internal/predict`.

O serviço `inference` é o roteador interno: API/Celery → roteador → API dedicada.
O cliente de negócio continua usando `http://127.0.0.1:8000/docs`:

```json
{
  "cycle_id": "UUID retornado pelo recebimento",
  "snapshot_id": "UUID retornado pelo recebimento",
  "model_key": "C1-CR1-P1",
  "requested_by": "operador"
}
```

Envie a `/v1/inference/predict` com `API_TOKEN`. O resultado contém versão, run,
hash do binário, código e dataset. Nenhuma URI ou nome de host vem do consumidor.
Pedidos dirigidos a outra chave/deployment são rejeitados pelo servidor dedicado.

Nova versão: treinar → revisar → promover → repetir `publish`. Durante a troca,
o processo antigo rejeita a aprovação revogada: há indisponibilidade breve, sem
servir silenciosamente uma versão antiga. Não há rollout sem interrupção nesta POC.
`publish` sem `-ModelKey` publica todos os modelos aprovados. Dimensione memória antes
de publicar as 30 APIs simultaneamente; cada uma tem limite de 512 MiB.

Após a primeira publicação, `compose.ps1` inclui automaticamente o arquivo de modelos
em start/stop/status/logs/validate. Para usar Docker diretamente:

```powershell
docker compose -f compose.yaml -f .runtime/models.compose.json ps
docker compose -f compose.yaml -f .runtime/models.compose.json logs -f NOME_SERVICO
```

## Validação

- `compose.ps1 validate`: dependências, serviços, unitários/integração e acessos autenticados.
- Pipeline CI: base descartável, treinamento no container Jupyter, aprovação explicitamente
  identificada como CI e publicação de uma API; previsão com rastreabilidade. Não promove dados locais.
- `docker compose run --rm --no-deps --entrypoint python tools tests/c3_system.py`:
  teste integrado isolado usando bancos/bucket aleatórios, removidos ao final. Inicia processos
  temporários, testa duas versões e recriação de MLflow/inferência. Não comprova rede Docker.
- `tools e2e`: aceitação das 30 séries, após revisão/aprovação/publicação de todas.

Volumes PostgreSQL e RustFS sobrevivem à recriação dos containers; não use `down -v`.
Backup externo, restauração e homologação do domínio continuam etapas próprias.

## Workbench externo e GKE

No Compose, DNS `mlflow`, `ingestion`, `rustfs` é interno à rede Docker. Fora dela,
configure endpoints alcançáveis separadamente. Para um kernel no Windows local use
portas 5000/8020/9000 de loopback e instale as dependências fixadas do projeto.
No GCP serão necessários endpoint privado/Gateway/Service, DNS, TLS, autenticação
do MLflow, identidades por serviço, Cloud SQL/PostgreSQL e adaptação do armazenamento
S3 para GCS. O Workbench externo não resolve automaticamente `svc.cluster.local`.
As imagens ainda não são publicadas no Artifact Registry Google. Model Registry
continua sendo o catálogo de modelos do MLflow, não um repositório de imagens.
