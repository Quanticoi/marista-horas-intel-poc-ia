# Sessão de aceite manual V3

Dados **DEMO**, contrato **provisório**. Nenhum resultado homologa regras V4.4.
Preencha PASS/FAIL/NOT_CHECKED em cada observação; testes de API não provam inspeção
visual. Use IDs retornados nesta sessão, nunca IDs de relatórios anteriores.

## Preparar a bancada

```powershell
.\deployment\scripts\compose.ps1 start
docker compose ps
```

Esperado: 11 serviços healthy. Abra [Jupyter](http://localhost:8888),
[MLflow](http://localhost:5000), [RustFS](http://localhost:9001),
[API](http://localhost:8000/docs) e [Dashboard](http://localhost:8088).
Jupyter: JUPYTER_TOKEN do `.env`; RustFS: AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY;
Dashboard: DASHBOARD_TOKEN. No Swagger, envie Bearer API_TOKEN; revisão técnica
usa OPERATOR_TOKEN. Não cole esses valores em células, relatórios ou screenshots.

Abra os notebooks em `/lab/tree/notebooks/`, editáveis. Shift+Enter renderiza
Markdown; Ctrl+S salva. Restart Kernel and Run All executa na ordem.
Execute 00 primeiro: SQL, tracking e gravação/leitura de artefato diagnóstico PASS.

## M01 — startup sem modelos (somente isolado)

Pré-condição: projeto descartável `marista-correcoes-isolated`, ownership conferido
pelo [controlador de reset](RESET_POC.md). Execute o ensaio de reset descrito em M10
com rebootstrap empty. Esperado: inferência healthy com cache vazio, Registry vazio,
sem treino automático. Não confundir readiness com modelo registrado/carregado.
Observação manual: **NOT_CHECKED**. Evidência automática: relatório do ensaio.

## M02 — treino individual e três séries diferentes

Abra 04, execute a primeira célula e a etapa 1 de seleção. A tabela vem de
`GET /v1/audit/scopes`: anote model_key legível e snapshot.id da extração SQL.
Na célula de configuração, **após** `params=Parameters.load()`, configure:

```python
params = params.model_copy(update={
    'model_name': 'hi.pt.demanda.DEMO-C1.DEMO-CR1.P1',
    'snapshot_id': 'COLE_O_ID_EXIBIDO_NA_SELECAO',
    'execute_write': True, 'confirmation': 'EXECUTE_DEMO',
    'request_key': 'manual-sessao-01-individual',
    'campaign_display_name': 'POC DEMO • Minha sessão • Individual',
    'alpha': 1.0,
})
```

Use a chave presente na tabela atual, caso o seed tenha sido alterado. A chave de
request identifica a operação: repetir mesmo conteúdo recupera job/versão;
alterar conteúdo com mesma chave falha 409. Nova chave + alpha=7 gera outra versão
da **mesma** identidade funcional. Guarde ambas as versões.

No 05, configure snapshot, execute_write/confirmation, request_key nova,
campaign_action='create', model_count=3 e campaign_display_name legível.
Esperado: três treinos reais, períodos diferentes, um experimento por ciclo,
três hashes de modelo; transformações ajustadas só no treino. A campanha não
promove modelos. A tabela Onde conferir contém todos os destinos.
Comparação no 06 exige mesmo escopo, snapshot, CSV, alvo e janela; não compare
MAE de cursos diferentes como se fosse o mesmo problema.
Observação manual: **NOT_CHECKED**.

## M03 — conferir MLflow visualmente

Na tabela Onde conferir, abra o experimento `HI/POC/PlanilhaTurmas/Demanda/<ciclo>`.
Em Runs, localize o run_name e filtre `tags.model_key = '<chave>'` ou
`tags.training_campaign_id = '<campanha>'`. Abra a run: Metrics contém MAE/RMSE
e baseline; Parameters contém features/target/split; Tags contém snapshot,
dataset hash, algoritmo, execution e correlação. Na seção Models/Registry,
abra o nome estável e versão exata. Compare source e run com os IDs da run.
Abra a descrição: nome DEMO, ciclo, snapshot, algoritmo e referência SQL.
Guarde os links da tabela e marque observação **PASS/FAIL/NOT_CHECKED**.

## M04 — conferir RustFS e bytes

No console, abra o bucket `pucpr-poc` e navegue até
`lineage/poc/planilha-turmas/catalog/cycles/<ciclo>/models/<model_key>/versions/v000N/manifest.json`.
Abra/baixe o JSON: confirme nome, run, versão, snapshot e files. Navegue pelas
**chaves exatas em files** para MLmodel/model.pkl/requirements.txt sob mlflow/.
Não converta `models:/` em caminho manualmente. O verificador usa URI obtida do
SDK, destino de proxy compartilhado com o servidor, listagem S3 e comparação
byte a byte com download pelo MLflow. Exporte Key/Bytes/SHA/Run/Model/Version.
Não modifique objetos. Observação: **NOT_CHECKED**.

## M05 — conferir PostgreSQL

Execute o [roteiro SQL](SQL_VALIDATION_V3.md) com os IDs da sessão.
Esperado: nomes/run/versões iguais entre sistemas; três contribuições não
triplicam linhas finais. `RECORDED` é índice persistido; `VERIFIED` exige auditoria
ao vivo. Verifique as tabelas do negócio, não apenas mlflow_db.
Observação: **NOT_CHECKED**.

## M06 — gerar proposta pela API

No 02, configure modo GENERATE_AND_VALIDATE, snapshot_id, model_name,
model_version explícita, execute_write=True, confirmation='EXECUTE_DEMO' e
request_key='manual-sessao-01-proposta'. Run All: HTTP202, job → COMPLETED,
proposal_id, payload paginado DRAFT, SQL e hashes reconciliados. Notebook não treina
nem grava a proposta diretamente; API/worker compõe e persiste transacionalmente.
Repita mesma chave: mesmo job/proposta; chave nova: proposta nova preservando a anterior.
Para três modelos, use `generate(cfg,payload,key)` com três model_selectors da
campanha; cada escopo contribui só suas linhas. Dois modelos no mesmo período
na mesma proposta são sobreposição e devem falhar.
Observação: **NOT_CHECKED**.

## M07 — recuperação sem Jupyter

No terminal, após salvar o notebook:

```powershell
docker compose stop jupyter
docker compose restart inference
docker compose ps
```

Pelo Swagger, envie nova geração com as mesmas versões e uma chave nova.
Consulte job até COMPLETED e `GET /v1/audit/model`: serviço healthy, registered,
artifact_verifiable, approved e cached são estados diferentes. O cache comporta
quatro versões por processo, expulsa a menos recente e registra hits/misses;
Registry não significa residente. Após reinício o primeiro acesso baixa o modelo.
Restaure `docker compose up -d --wait jupyter`. Aprovação/revogação: somente DEMO,
no 07, pedido e revisão explícitos com credencial separada; modo APPROVED deve
falhar após revogação mesmo se cache quente. Isso não é aprovação acadêmica.
Observação: **NOT_CHECKED**.

## M08 — capacidade

Na stack isolada, 05 com model_count=30 usa os 30 escopos sintéticos cadastrados.
Observe contagens/progresso, métricas CPU/RSS por run e hashes. Limite de dois
workers, não 500 residentes. A evidência V2 de 500 identidades usa o mesmo dataset
agregado e um único SHA de model.pkl: serve como baseline de transporte/retomada,
**não certifica V3 nem 500 comportamentos diferentes**. Não repetir custo sem necessidade.
Observação: **NOT_CHECKED**.

## M09 — falhas controladas

Somente stack isolada: MLflow indisponível, objeto ausente/corrompido, versão
inexistente, tag compartilhada divergente, revogação e snapshot errado. Execute
o teste automatizado correspondente; nunca corrompa binário na stack principal.
Sem Bearer: 401/403. Versão inexistente: NOT_FOUND/404; referência perdida: MISSING;
tags/bytes divergentes: MISMATCH; legado insuficiente: LEGACY_PARTIAL.
No notebook00 MLflow indisponível deve bloquear antes de fit; sem SQLite fallback.
Observação: **NOT_CHECKED**.

## M10 — reset

09 é sempre preview/read-only. No terminal, use o controlador externo conforme
[RESET_POC](RESET_POC.md), projeto **marista-correcoes-isolated**, modos reset-data
com empty e factory-reset com demo-ready. A confirmação deve ser a exigida pelo
plano atual. Conferir ownership, volumes, hashes de arquivos protegidos e ausência
de dados anteriores. Nunca reaproveitar plano expirado nem resetar marista.
Observação: **NOT_CHECKED**.

Ensaio automatizado reproduzível (somente o projeto isolado está aceito pelo script):

```powershell
python tests/acceptance/isolated_stack.py
python tests/acceptance/reset.py --report-version v3
```

Para observar pessoalmente o estado vazio, use o controlador interativo e pare
no rebootstrap empty, antes de executar qualquer seed/treino:

```powershell
python deployment/scripts/reset_poc.py preview --environment poc --project marista-correcoes-isolated --mode reset-data
python deployment/scripts/reset_poc.py execute --environment poc --project marista-correcoes-isolated --plan-id UUID_DO_PLANO_ATUAL --execute --reinitialize empty
```

O segundo comando exige a confirmação do plano. Não substitua o projeto por marista.
O ensaio automatizado já executado consta em `artifacts/reports/v3/reset-isolated-proof.json`;
ele não substitui uma observação humana do momento empty.

## M11 e M12 — auditoria reversa e pacote

08: lineage_kind='proposal', proposal_id da sessão; Run All. A auditoria mostra
inferências, modelos/versões, runs, experimentos, snapshot e arquivos. Repita
lineage_kind='model' com external_id=model_key e model_version; depois 'run' com
external_id=run_id. A consulta parte da identidade, não de uma busca por hashes.
Dashboard: Catálogo auditável, filtre chave/run/campanha/proposta/correlação;
links abrem run e Registry. Aba Logs usa os mesmos filtros com eventos completos.

O 08 exporta `/reports/v3/manual-session-<UUID>.json/.md/.csv`, no host
`artifacts/reports/v3`. Preencha observações reais; o padrão é NOT_CHECKED.
Inclui sessão UTC, base Git e hash dos fontes, ambiente DEMO, IDs e evidências.
AUTO_PASS é prova executada por código; MANUAL_PASS requer observação humana/UI;
MANUAL_NOT_CHECKED é conferência pendente; BLOCKED informa impedimento concreto.
Observação final: **NOT_CHECKED** até percorrer as telas.

## Contrato HTTP de auditoria

Todas as rotas abaixo exigem `Authorization: Bearer API_TOKEN`, fornecido pelo
SDK do notebook sem imprimir o valor. O Swagger mostra os tipos e exemplos de schema.

| GET | Filtros / retorno |
|---|---|
| /v1/audit/scopes | Escopos sintéticos derivados de catálogo SQL com histórico SYNTHETIC; nomes e PKs |
| /v1/audit/inventory | model_key, run_id, snapshot_id, campaign_id opcionais; limit 1–500, offset 0–100000; versões catalogadas |
| /v1/audit/model | model_key (até160, códigos seguros), version (inteiro positivo textual até12 dígitos); status, checks, metadata, files, serving, approved |
| /v1/audit/proposal/{proposal_id} | UUID; status, linhas declaradas/persistidas, contribuições e auditorias de modelos/inferências/manifest |

HTTP200 transporta a auditoria, inclusive NOT_FOUND/MISSING/MISMATCH/LEGACY_PARTIAL;
isso **não** significa integridade aprovada. VERIFIED só após reconciliação real.
HTTP401: credencial ausente/incorreta. HTTP422: parâmetros inválidos. HTTP503:
dependência indisponível que impediu executar a auditoria; diagnóstico sanitizado.
Modelos desconhecidos consultados diretamente retornam NOT_FOUND; modelo referido
por proposta existente e ausente do Registry é MISSING. O inventário SQL apresenta
RECORDED até a reconciliação viva. Cache e aprovação não são inferidos de health.

Exemplo sem segredo, a partir do resultado atual do notebook:

```python
from urllib.parse import urlencode
result = call(cfg, 'GET', '/v1/audit/model?' + urlencode({
    'model_key': params.model_name, 'version': params.model_version}))
display({key: result[key] for key in ('status', 'registered', 'approved', 'artifact_verifiable', 'serving')})
```
