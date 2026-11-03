# Consultar a jornada no MLflow

Abra [MLflow](http://127.0.0.1:5000). O servidor local reúne Tracking e Model Registry;
seus metadados ficam no PostgreSQL e os artefatos no RustFS.

## Encontrar a execução

1. Abra o experimento `planilha-turmas-proxy-v1`.
2. Identifique a run pelo `run_id` ou pela tag `execution_id` exibidos no notebook.
3. Para ir diretamente à execução, use o link fornecido na etapa de tracking ou
   no resumo final da Jornada Completa.

O experimento `journey-diagnostics-proxy` contém as verificações de disponibilidade:
são runs de diagnóstico com gravação e leitura de um pequeno artefato, não treinos.

## O que conferir

| Informação | Registro |
|---|---|
| Modelo | Parâmetros `algorithm`, `alpha`, `seed`, `features` e `target` |
| Avaliação | Métricas `mae`, `rmse` e `training_seconds` |
| Inferência | Métricas `inference_rows` e `inference_seconds` |
| Dados e SQL | Tags `snapshot_id`, `dataset_sha256`, `query_sha256` e `query_version` |
| Código | Tag `code_version`, hash do código utilizado |
| Correlação | Tags `execution_id`, `correlation_id`, ciclo e escopo |
| Referências | SQL e CSV da extração em `reference` |
| Avaliação detalhada | Artefato `evaluation.json` |
| Evidência final | Resumo JSON em `evidence` |

As métricas são calculadas com dados sintéticos e demonstram funcionamento da
integração. Não constituem validação de qualidade para dados institucionais.

## Modelo registrado

No Model Registry, localize `planilha-turmas-demo` e a versão indicada pelo notebook.
A versão está vinculada à run e inclui o pipeline ajustado, assinatura de entrada/
saída e exemplo. A referência usada para inferência é
`models:/planilha-turmas-demo/VERSAO`, com versão explícita.

O notebook remove o objeto treinado da memória, recarrega essa referência e compara
suas previsões com as do serviço de inferência. Registro e carregamento não
significam aprovação ou promoção para uso operacional.

## Ligar o modelo à Planilha Turmas

A geração persistida na aplicação guarda `execution_id`, `run_id`, experimento,
nome/versão do modelo, snapshot e regra aplicada. Consulte a geração pela API e
use o mesmo `execution_id` no dashboard para reunir os eventos da jornada.

Cada Run All cria uma nova run e proposta. Repetir somente a persistência com o
mesmo identificador e conteúdo é idempotente. Runs e modelos de demonstrações
anteriores podem permanecer no servidor; use sempre os IDs da execução desejada.

[Executar a jornada](JOURNEY.md) · [API e interfaces](../../README.md#interfaces-e-acesso).
