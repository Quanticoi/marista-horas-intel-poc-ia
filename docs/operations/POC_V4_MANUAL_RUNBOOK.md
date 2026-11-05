# Roteiro V4 — do SQL à proposta

Execute na ordem abaixo, usando as versões distribuídas em `workspace/notebooks`.
As planilhas fornecem estrutura de planejamento; o histórico é sintético, seed 42.
Os [limites funcionais](../architecture/FUNCTIONAL_COVERAGE.md) permanecem explícitos.

## 1. Preparar

Na raiz do repositório, com Docker Desktop ativo:

```powershell
.\deployment\scripts\compose.ps1 start
# Se houve alteração de código/imagens:
.\deployment\scripts\compose.ps1 rebuild
```

Instalação nova usa `init`. Os serviços devem ficar healthy; rebuild não treina nem
apaga dados. Coloque as três planilhas em `data/reference/`, montada como `/reference:ro`.
Credenciais são fornecidas pelo `.env`; não as escreva nas células.

Abra [Jupyter](http://localhost:8888/lab/tree/notebooks/00_ambiente.ipynb).
Cada notebook deve funcionar com **Restart Kernel and Run All**.

## 2. Conferir e preparar a origem — 00 a 03

- **00:** testa SQL de origem/destino, SDK/servidor MLflow e round-trip de artefato.
  Uma falha bloqueia o treino; não há fallback para tracking local.
- **01:** importa referências de forma idempotente. Confira 107 registros e o
  dicionário real de 31 entidades/175 campos, divergente das 30 citadas na spec.
- **02:** confira 70 ofertas, 13 registros em quarentena, P164/P110A e cursos/turnos.
- **03:** cria ou recupera snapshot determinístico: 227 observações históricas e
  58 futuras. A fonte fica em PostgreSQL, com hashes e proveniência.

## 3. Treinar — 04 ou 05

**04** treina uma identidade; **05** treina os três cursos 2248, 2348 e 2287.
Para gerar a proposta completa, use **05**. Escolha métricas nos checkboxes antes
de executar a célula de treinamento; a seleção altera o cálculo e o tracking.

O padrão `CAMPAIGN_MODE='NEW'` cria uma campanha e um experimento **a cada execução
da célula de treino**, mesmo sem reiniciar o kernel. O notebook mostra a chave antes
do fit e links clicáveis ao concluir. Regulares são avaliados por coorte/ciclo;
adicionais por oferta/ciclo. O último ciclo histórico é holdout; não há treino com alvo futuro.

Para retomar a mesma campanha, use `CAMPAIGN_MODE='RESUME'` e preencha
`RESUME_REQUEST_KEY` com a chave exibida anteriormente. Mantenha snapshot, escopos e
métricas iguais. Chave inexistente ou configuração divergente é rejeitada.
Resultados concluídos são reutilizados; essa é uma retomada explícita, não outro ensaio.

## 4. Avaliar, aprovar e disponibilizar — 06 a 08

**06** mostra baseline, métricas por alvo e agregação de observações comparáveis.
Métricas sintéticas não comprovam qualidade institucional.

**07** começa em inspeção. Confira modelos/versões, métricas e motivo; habilite
`APPROVE_DEMO=True` para a decisão técnica. O operador é autenticado separadamente.

**08** começa em leitura. Habilite `DEPLOY_DEMO=True` para disponibilizar as versões
aprovadas e `GENERATE=True` para gerar a proposta. O primeiro modelo usa PRELOAD,
os demais LAZY. A chave de geração padrão deriva da campanha: reexecutar recupera
o mesmo job; nova campanha gera outra proposta. Não altera revisões anteriores.

## 5. Consultar e auditar — 09 e 10

O contexto de **08** leva `proposal_id` ao **09**. A tabela usa somente HTTP;
confere paginação/schema/hash e permite filtros acadêmicos. Confira P164: uma
oferta, três atividades e planejados 41/21/20, sem somá-los como 82 estudantes.
Confira 2287/período 2: regular comum à coorte e adicionais por disciplina.

**10** confronta proposta, snapshot, fontes, inferências, Registry, runs e RustFS.
`VERIFIED` significa integridade técnica. S03 permanece pendente de capacidade e
anuência; grupos não são inventados.

## 6. Limpar ensaios — 11

Run All do **11 apenas apresenta o procedimento**. O reset efetivo é executado pelo
controlador no PowerShell porque precisa parar/reiniciar os serviços, inclusive
Jupyter. Use [reset-experiments](RESET_POC.md) para apagar MLflow/RustFS/resultados e
preservar as cinco tabelas da origem. Depois, **04/05** podem ler a mesma carga SQL.

## Testes reproduzíveis

```powershell
docker compose run --rm --no-deps -v "${PWD}:/app:ro" -v "${PWD}/data/reference:/reference:ro" --entrypoint python tools -m pytest tests/unit tests/integration -q -o cache_dir=/tmp/pytest
docker compose run --rm --no-deps -v "${PWD}:/app:ro" --entrypoint /usr/local/bin/_entrypoint.sh jupyter python -m pytest tests/integration/test_workbench_v4.py -q -o cache_dir=/tmp/pytest-workbench
```

A execução automatizada dos 12 notebooks com escritas DEMO explícitas é:

```powershell
docker compose run --rm --no-deps --entrypoint /usr/local/bin/_entrypoint.sh jupyter python -m src.workbench.v4_notebook_suite --approve-demo
```

Esse comando cria novos experimentos, treina, aprova e gera proposta; não é um
comando apenas de leitura. Para provar o reset somente no projeto descartável:
`python tests/acceptance/v4_adjustments.py --reset-isolated`.

[Aceite V4](../../artifacts/reports/v4/acceptance-v4.md) e
[ajustes posteriores](../../artifacts/reports/v4-adjustments/README.md) registram
resultados separados. Inspeção visual, CI remota e execução Linux não são presumidas.
