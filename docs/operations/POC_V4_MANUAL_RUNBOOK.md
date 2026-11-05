# V4 — execução por fases

Estado: implementação parcial. O fluxo V3 continua disponível; a jornada V4 não foi substituída por notebooks vazios.

## Bloqueio da importação

Os oito arquivos da seção 0.1 da SPEC não foram encontrados em `reference/`, `data/reference/` ou `dev/reference/`. A busca adicional nos arquivos do repositório não encontrou XLSM/XLSX/PDF nem o diagnóstico.
A ausência impede verificar 107 linhas, P164, P110A e o dicionário de 30 entidades/175 campos. Não usar os números citados na SPEC para fabricar uma importação.

Disponibilize o pacote em `reference/` ou informe o diretório real. O inventário é somente leitura e não executa macros:

PowerShell e Linux, na raiz do repositório:

```text
python -m src.academic.sources
python -m src.academic.sources --root CAMINHO_DO_PACOTE
```

Saída: `artifacts/reports/v4/source_inventory.json`. Exit code 2 significa fonte ausente/ambígua. FOUND comprova presença e SHA256, não integridade acadêmica. Não há cópia ou carga SQL automática neste checkpoint.

## Métricas independentes implementadas

`config/metric_catalog.yaml` e `config/metric_profiles/*.yaml` usam sintaxe JSON, subconjunto de YAML. Catálogo 1.0: MAE, RMSE, MedAE, WAPE, sMAPE, R², Bias e P90 do erro absoluto.
Seleção incompatível, duplicada ou desconhecida interrompe. WAPE com denominador zero e R² com amostra insuficiente/constante são NOT_EVALUATED.
sMAPE define contribuição zero para par real=previsto=0. Bias é previsto menos observado.
Consolidação reúne observações apenas da mesma tarefa, target, horizonte, split e classe de dado; os percentis são globais dos erros, não médias de percentis de modelos.

Perfis academic_impact e compute_resource reservam requisitos: não anunciam cálculo implementado de impacto acadêmico ou instrumentação de recursos. A integração em notebook, executor Workbench e MLflow permanece pendente; não há treino V4 executado.

## Reprodução da prova isolada

PowerShell:

```powershell
docker run --rm --network none -v "${PWD}:/app:ro" -v "${PWD}/artifacts/reports/v4:/reports" -w /app --entrypoint /usr/local/bin/_entrypoint.sh marista-jupyter:compose python -m pytest tests/unit/test_v4_foundations.py -q -o cache_dir=/tmp/pytest-v4 --junitxml=/reports/foundations-junit.xml
```

Linux: use o mesmo comando substituindo `${PWD}` por `$PWD`.
Imagem Jupyter já existente; nenhum serviço foi recriado, nenhum banco ou volume foi alterado.
12 testes executados, sem prova acadêmica/E2E. Requisitos CPU/RAM da futura campanha ainda devem ser medidos, não inferidos destes testes.

## Próximos gates

A: receber/ler fontes, preservar linhas/células, importar com migração aditiva e validar estrutura.
B: simulação condicionada e cold start, após A.
C: executor local no Workbench, métricas integradas, três modelos reais da estrutura importada.
D: governança e serving, preservar migration009/RECONCILING.
E: contrato V2, notebook09 somente HTTP e auditoria.
F: evidências E2E, CI e checklist manual separado.
