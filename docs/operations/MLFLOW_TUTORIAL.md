# MLflow: onde clicar e o que observar

Roteiro para MLflow 3.11.1 desta POC. Os nomes abaixo são os rótulos em inglês;
a posição pode variar com a largura da janela. Tutorial baseado na documentação
e nos experimentos registrados; a migração Compose foi validada em 26/10/2026.

## 1. Abrir

1. Na raiz do projeto, execute `docker compose up -d --wait` após a migração inicial.
2. Abra http://127.0.0.1:5000 no navegador. Não há login no MLflow local desta POC.
3. Clique em **Experiments** na navegação.
4. Se estiver em **Default**, volte à lista de experimentos: Default está vazio.
5. Clique em **public-macrodata-timeseries**. O link direto do banco migrado é
   http://127.0.0.1:5000/#/experiments/2.

Você deve encontrar as nove execuções do laboratório público. O experimento
**pucpr-synthetic**, ID 1, contém as 30 execuções acadêmicas sintéticas anteriores.
Reexecuções futuras acrescentam runs; esses números são a referência inicial.
Limpe filtros de data/pesquisa se não aparecerem os resultados.

## 2. Entender uma execução

1. Na tabela de runs, clique no nome **realgdp-ridge**.
2. Confira o status **FINISHED** e os horários. FINISHED significa execução
   concluída, não aprovação de qualidade.
3. Abra a seção **Parameters**: procure `series`, `algorithm`, `horizon`,
   `train_rows`, `validation_rows` e `test_rows`.
4. Abra **Metrics**: confira `validation_mae`, `test_mae` e `test_rmse`.
5. Abra **Tags** e procure `dataset_sha256`, `synthetic` e `selected_on_validation`.

`horizon=1` significa prever o trimestre seguinte usando o passado disponível.
MAE mede erro absoluto médio; RMSE penaliza mais erros grandes. Menor é melhor
para a mesma série e unidade. Não compare erro de PIB em dólares com desemprego
em pontos percentuais. `selected_on_validation=true` indica a escolha no período
de validação, antes de observar o teste.

## 3. Comparar os métodos

1. Volte ao experimento pelo breadcrumb ou pelo botão Voltar do navegador.
2. No campo de pesquisa, digite `params.series = 'realgdp'` e aplique a busca.
3. Marque as caixas das execuções **realgdp-persistence**, **realgdp-ridge** e
   **realgdp-random_forest**.
4. Clique em **Compare** na barra de ações da seleção.
5. Na comparação, selecione as métricas de validação e teste. Compare parâmetros
   e métricas lado a lado. Se as colunas não estiverem visíveis na lista, use
   **Columns** para habilitá-las.
6. Repita a busca para `realcons` e depois `unemp`.

Na execução inicial, Ridge venceu em validação para PIB/consumo. No desemprego,
Random Forest venceu por pequena margem na validação, mas Ridge teve menor erro
no teste. Isso não autoriza trocar retrospectivamente a escolha pelo teste.
Persistência é o baseline: prever o próximo valor igual ao último observado.

## 4. Ver arquivos, gráficos e dados

1. Abra novamente uma execução pública.
2. Clique em **Artifacts** (ou expanda a seção de artefatos na página da execução).
3. Expanda **dataset** e selecione `provenance.json`: origem, versão e SHA-256.
4. Selecione `macrodata.csv` para consultar/baixar a entrada preservada.
5. Expanda **evaluation** e selecione o CSV de previsões: `actual`, `predicted`
   e `residual`.
6. Expanda **plots**, selecione `test-predictions.png` e visualize o gráfico.
7. Use o botão de download do arquivo quando disponível.

Se as métricas aparecem mas o artefato falha, verifique `docker compose ps` e
`docker compose logs --tail 100 mlflow rustfs`. Metadados ficam no PostgreSQL;
arquivos ficam no RustFS. Ambos são necessários. Não edite caminhos S3 no banco.

## 5. Encontrar os modelos registrados

1. Na navegação principal, clique em **Models** / **Model Registry**. Não confunda
   com a aba de modelos logados dentro de um único experimento.
2. Busque **public-macrodata-realgdp-ridge**.
3. Clique no nome do modelo e depois no número da versão, inicialmente **1**.
4. Confira a origem e clique no link do run associado para voltar ao treinamento.
5. Observe os aliases: o laboratório não atribui `champion` automaticamente.

Existem seis modelos públicos registrados: Ridge e Random Forest para três séries.
Persistência não gera um arquivo treinado. Os modelos acadêmicos usam nomes como
`C1-CR1-P1` e possuem seu próprio fluxo de aprovação.

## 6. Aprovar não é apenas clicar em um alias

Neste projeto, promoção acadêmica deve passar pelo comando auditado, que mantém
Registry e banco de planejamento consistentes. Alterar somente um alias pela UI
não publica o modelo corretamente para nossa API.

Após revisão explícita do operador, exemplo:

```powershell
docker compose run --rm tools promote C1-CR1-P1 1 operador "Justificativa da aprovação"
```

Não execute como exercício sem intenção de aprovar. Os modelos públicos são
um laboratório separado e não são candidatos ao catálogo de matrículas.

## 7. Rodar outra experiência depois

O MLflow mostra e organiza o que seu código registra; clicar em Experiments não
executa treinamento. Quando decidir trabalhar nos notebooks, abrir/reexecutar
`08_public_timeseries_lab.ipynb` no Jupyter cria novos runs e versões.
Nesta migração, nenhum notebook é reexecutado ou reescrito.

Referências oficiais:
- [Tracking e interface](https://mlflow.org/docs/latest/ml/tracking/).
- [Registry, versões e aliases](https://mlflow.github.io/mlflow-website/docs/latest/ml/model-registry/).
