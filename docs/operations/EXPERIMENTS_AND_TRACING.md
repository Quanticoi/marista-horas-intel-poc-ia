# Campanhas, repetição e Traces

## Nova campanha versus retomada

O padrão dos notebooks 04/05 é `CAMPAIGN_MODE='NEW'`. Cada execução da célula de
treinamento gera outra chave, campanha SQL e experimento MLflow. Mesmo reexecutando
somente essa célula, o resultado anterior é preservado. O nome do experimento contém
ciclo, data UTC e UUID; runs filhas representam lotes e modelos.

`RESUME` exige `RESUME_REQUEST_KEY` existente e a mesma configuração. Reutiliza
checkpoint e resultados concluídos; não é novo experimento. Alterar métricas,
snapshot ou itens sob a mesma chave falha. Uma chave inexistente não cria campanha.
O código limita tentativas; falha durante registro pode exigir diagnóstico antes da retomada.

| Ação repetida | Efeito |
|---|---|
| Importar as mesmas referências | Valida/reutiliza; conteúdo divergente sob identidade existente falha |
| Gerar a mesma simulação | Recupera snapshot determinístico |
| Treinar com NEW | Novo experimento, runs e versões |
| Treinar com RESUME | Recupera a campanha identificada; itens concluídos não repetem fit |
| Aprovar/disponibilizar | Usa versão explícita e controles de decisão; não é consequência do registro |
| Gerar com a mesma chave/payload | Retorna o mesmo job/proposta |
| Gerar com chave nova | Cria proposta nova, preservando anteriores |
| Consultar 09/10 | Leitura e verificação; não treina |

A chave de geração padrão deriva da campanha. O notebook 08 a reutiliza para que
um retry não duplique proposta. Novo treino limpa o contexto de proposta anterior;
o 08 publica a nova antes de o 09 consumi-la.

## Onde encontrar o experimento

Use o link **Abrir experimento** exibido ao concluir 04/05. A UI é
`MLFLOW_UI_BASE_URL` (localhost:5000); `MLFLOW_TRACKING_URI` (mlflow:5000) é interno.
O experimento de campanha é criado pelo executor, não pela variável legada
`MLFLOW_EXPERIMENT_NAME`. Os diagnósticos do 00 ficam separados.

Campanhas anteriores à mudança de política podem estar em
`HI/POC/PlanilhaTurmas/academic-components/2024-2`. A antiga chave fixa recuperava
uma campanha já concluída; não sobrescrevia seus modelos. Agora só RESUME faz isso
explicitamente. Não se renomeiam nem se apagam esses experimentos durante rebuild.

## Finalidade dos Traces

Runs armazenam parâmetros/métricas/artefatos de treinamento. Traces mostram a
sequência de operações, duração e falhas de uma execução. O fluxo operacional
propaga contexto W3C do worker para inferência e registra consultas, carga e predict.
O experimento `HI/POC/Operations/V4` reúne essa instrumentação.

`trace_id` liga o job às chamadas reais; `campaign_id`, `run_id`, `inference_id`
e `proposal_id` permitem atravessar as fronteiras. Traces não substituem o banco
de negócio nem autorizam uma versão. Não armazenam credenciais ou payload acadêmico integral.

[Tutorial MLflow](MLFLOW_TUTORIAL.md) · [Organização de modelos](MLFLOW_MODEL_ORGANIZATION.md)
· [Auditoria](../architecture/LINEAGE.md).
