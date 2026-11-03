# Aceite de Tracing e persistência — 03/11/2026

Ambiente real Docker Compose, MLflow servidor/SDK 3.11.1. Rebuild e deploy
executados; notebook principal executado em kernel novo por nbclient no Jupyter.

| Evidência | Resultado |
|---|---|
| Execution/proposta | d6260507-b9f4-4011-a3f6-b3dd511400d5 |
| Run | 03012b122e6143b2919807cd91973451 |
| Experimento | 4, planilha-turmas-proxy-v1 |
| Modelo | planilha-turmas-demo, versão 8 |
| SQL origem | 1.050 registros DEMO |
| Proposta/API | 90 linhas, DRAFT |
| Tracing | 12 traces, 21 spans da jornada |
| Object Store | SHA256 igual no proxy e RustFS para 3 arquivos |
| Banco de negócio | 90 linhas e valores conferidos em conexão SQL independente |
| Jornada | 10 testes PASS |
| Suíte geral | 44 testes PASS |
| HTTP | 19 checks PASS |

Spans de inferência: reload and inference → model.load (local) e inference.http
→ model.load/model.predict (serviço). Spans de reconciliação: API reconciliation
→ api.http → postgres.query. IDs de contexto iguais entre processos e relações
pai/filho consultadas pelo SDK no servidor. Nenhum input/output de dados capturado.

Primeira tentativa identificou ausência de spans remotos. Corrigida configuração
do destino antes da adoção do contexto W3C, conforme comportamento do SDK 3.11.1.
Reteste completo passou. Verificação adicional de falha gera ERROR com tipo de
exceção sem mensagem sensível; repetir etapa produz outro trace/attempt.

A etapa 7b lê RustFS `pucpr-poc/mlflow/4/models/m-378e0cf868604331bf7c52e0c1421114/artifacts/`
e compara `MLmodel`, `model.pkl` e `requirements.txt` com downloads pelo MLflow.
A etapa 10b lê `planejamento_db.planning.proposal_generations/proposal_lines` após
commit e confere identidade, contagem e valores. Teste de conteúdo alterado é rejeitado.

[Run](http://127.0.0.1:5000/#/experiments/4/runs/03012b122e6143b2919807cd91973451) ·
[Traces](http://127.0.0.1:5000/#/experiments/4/traces) ·
[Resumo e hashes](journey-latest.json) · [Testes da jornada](journey-junit.xml) ·
[Suíte](compose-junit.xml) · [HTTP](access-check.json).

Os links de seleção de trace foram conferidos no JavaScript da UI instalada:
`selectedEvaluationId` e `compareRunsMode=TRACES`. O relatório JSON foi atualizado
por consulta ao SDK, sem novo treinamento. O notebook executado mantém a saída
original do ensaio; o notebook fonte contém os links corrigidos.

Não executado: carga de 500 modelos, orquestração de campanhas, reset dos dados,
inspeção visual da UI por navegador ou validação de regras institucionais reais.
Convenção de escala documentada no guia; não constitui benchmark de capacidade.
