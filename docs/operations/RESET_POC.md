# Reset da POC

**Rebuild preserva dados. Reset apaga dados.** O notebook 11 mostra o procedimento;
executar suas células não realiza a limpeza. O controlador roda no host para
parar os serviços, inclusive Jupyter, e conferir o escopo Docker real.

## Modo padrão: reset-experiments

| Preserva | Remove |
|---|---|
| Arquivos/linhas/dicionário de referência SQL | Experimentos, runs, métricas, Traces e Model Registry |
| Snapshots e observações sintéticas SQL, mesmos IDs e hashes | Artefatos RustFS, inclusive versões antigas e delete markers |
| Estrutura do banco e migrations aplicadas | Campanhas, modelos catalogados, aprovações, deployments, inferências e propostas |
| `.env`, fontes, notebooks editados, evidências locais e backups existentes | Filas operacionais e contexto ativo de campanha/proposta no workspace |

As tabelas preservadas em `planejamento_db.planning` são:
`academic_source_files`, `academic_reference_rows`, `academic_data_dictionary`,
`academic_simulation_snapshots` e `model_training_observations`. As views canônicas
continuam funcionando sobre elas. Os demais dados de negócio são limpos para não
deixar referências penduradas a modelos apagados. Backups sob `backups/` no RustFS
são preservados; se não existirem, o bucket fica sem objetos após este modo.

Não há exportação/reimportação da origem. O controlador compara contagens e hashes
de todas as cinco tabelas antes/depois. `mlflow_db` é recriado e inicializado por
`mlflow db upgrade`; nenhuma migration própria reproduz tabelas do MLflow.

## Executar em PowerShell

Finalize treinos/jobs em andamento. Na raiz do projeto:

```powershell
$plan = python deployment/scripts/reset_poc.py preview --environment poc --project marista --mode reset-experiments | ConvertFrom-Json
$plan.plan_id
$plan.effects
```

O preview apenas inventaria e grava um plano. Confira o escopo e então execute:

```powershell
python deployment/scripts/reset_poc.py execute --environment poc --project marista --plan-id $plan.plan_id --execute
```

Digite a frase solicitada: **LIMPAR EXPERIMENTOS DA POC MARISTA**.
Não use `demo-ready` com esse modo: a origem deve ser preservada, não semeada novamente.

Consulte o resultado:

```powershell
python deployment/scripts/reset_poc.py status --environment poc --project marista --plan-id $plan.plan_id
```

Esperado: `RESET_PASS`, `source_preservation=COUNTS_AND_HASHES_IDENTICAL`, nenhuma
run/modelo/trace ou proposta anterior. O MLflow pode apresentar `Default` vazio.
O Jupyter volta disponível; abra 04/05 para iniciar novos experimentos a partir da
origem existente. Células e relatórios salvos continuam sendo evidências históricas;
seus IDs antigos deixam de existir nos serviços após a limpeza.

## Outros modos, explicitamente destrutivos

| Modo | Efeito |
|---|---|
| `reset-data` | Apaga também a origem SQL e objetos de dados; mantém volumes |
| `factory-reset` | Remove os containers e três volumes exclusivos validados |

Esses modos exigem a frase **APAGAR TODOS OS DADOS DA POC MARISTA**. O rebootstrap
`empty` deixa schemas/serviços prontos; `demo-ready` cria apenas a seed legada,
não importa as referências V4. Não há treinamento automático.

## Validação de escopo e falhas

O controlador confere labels, diretório, consumidores dos volumes, nomes de bancos,
bucket e inventário. Planos expiram em 15 minutos; alteração de dados/arquivos
protegidos exige novo preview. Projeto compartilhado ou overlay desconhecido é
rejeitado. `factory-reset` recusa backups internos ao volume até exportação externa.

`RESET_PARTIAL` registra passos concluídos; não significa rollback distribuído.
Diagnostique os serviços antes de gerar outro plano. Relatórios ficam em
`artifacts/reports/reset/`, fora dos volumes. O teste automatizado de limpeza seletiva
usa exclusivamente `marista-correcoes-isolated`; não limpa o ambiente principal.
