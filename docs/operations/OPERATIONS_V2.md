# Operações V2 pelo Jupyter

Abra [Jupyter](http://localhost:8888). Execute em kernel novo. Cada notebook contém
configuração tipada `Parameters`, preflight, operação, evidência e relatório.
Edite o bloco de configuração para usar, por exemplo:

```python
params = Parameters(
    mode="GENERATE_AND_VALIDATE",
    snapshot_id="fb931e1e-43d0-5ff8-938c-0d2ba4a68794",  # seed DEMO; confira 03
    model_name="planilha-turmas-demo",
    model_version="13",  # exemplo; escolha versão existente no seu ambiente
    execute_write=True,
    confirmation="EXECUTE_DEMO",
    request_key="demonstracao-2026-1-tentativa-01",
    requester="cientista-demo",
    capacity=40,
)
```

Não copie IDs de relatórios isolados para a stack principal. Versões/snapshots
devem existir no ambiente consultado. Parâmetros também podem vir de `V2_*`
no processo executor; credenciais somente de `.env`, nunca do código da célula.

## API e estados

Todas as rotas de negócio usam Bearer API_TOKEN. Somente `/review` exige
OPERATOR_TOKEN; um API_TOKEN comum recebe403. Credenciais nunca são impressas.
`X-Correlation-ID` correlaciona notebook, job, eventos e resposta.

| Operação | Request / resultado |
|---|---|
| POST /v1/proposals/generations | Generation; Idempotency-Key obrigatório;202 com job/status_url |
| GET /v1/proposals/generations/{id} | PENDING/RUNNING/COMPLETED/FAILED/CANCELLED; eventos, tentativa, proposal_id, trace_id |
| GET /v1/proposals/{id}/application-view | Contrato Pydantic/JSON Schema paginado; limit1–500/offset |
| GET /v1/proposals/{id}/lineage | Versões e atribuição por linha |
| POST /v1/training/campaigns | snapshot/ciclo/model_keys/ridge ou dummy/alpha/paralelismo;202 |
| GET /v1/training/campaigns/{id}/items | Estado, tentativa, run, versão, métricas, hash; limit1–500/offset |
| POST /v1/training/campaigns/{id}/pause | PAUSING→PAUSED após itens ativos concluírem |
| POST /v1/training/campaigns/{id}/resume | Retoma pendentes da mesma campanha |
| POST /v1/training/campaigns/{id}/cancel | CANCELLING→CANCELLED; resultados já concluídos preservados |
| POST /v1/training/campaigns/{id}/retry-failed | Nova janela limitada de tentativas dos itens FAILED; eventos anteriores preservados |
| POST /v1/governance/requests | Modelo/versão/APPROVE,REVOKE,ROLLBACK/solicitante/justificativa |
| POST /v1/governance/requests/{id}/review | Operador autenticado; approve e confirm=REVIEW_EXPLICIT_VERSION |
| GET /v1/lineage/graph | kind, external_id, version; entidades/arestas paginadas |

Erros:401 autenticação comum;403 operador/aprovação ausente;404 identidade ausente;
409 conflito de chave/transição/snapshot;422 parâmetros inválidos;503 dependência.
Falha depois de aceitar202 aparece no job, com código sanitizado e tentativas.
Consulta de resultado nunca treina. Repetir chave/payload recupera o resultado;
nova chave gera uma nova versão de proposta, sem alterar original/revisões humanas.

## Campanhas e controle

No05 selecione snapshot_id, model_count, algorithm, alpha, parallel_jobs≤2,
campaign_action=create e confirmação. request_key estável define nomes
hi.demo.campaign.<hash-da-chave>.<índice>. Registre o campaign_id mostrado.
Para pausar/retomar/cancelar, selecione esse campaign_id e a ação correspondente;
não crie nova chave para continuar uma campanha já submetida.

Para04 escolha model_name=hi.demo.<identidade>, snapshot e parâmetros; um item
de campanha fornece a mesma proteção de repetição. Baseline e avaliação respeitam
o corte temporal. Séries curtas/incompletas são rejeitadas no caminho Ridge;
o pipeline legado mantém fallback sazonal, sem atribuí-lo ao novo caminho.

## Governança

06 compara runs do mesmo snapshot e janela e elege candidato, sem promover.
07 seleciona versão e verifica bytes; action=request cria pedido auditável.
Em outra execução, informe approval_id e governance_action=approve/reject com
confirmação. A credencial de operador identifica o revisor. REVOKE bloqueia o modo
APPROVED; ROLLBACK exige versão já aprovada anteriormente. DEMO explícito continua
separado de aprovação, para experimentos sem publicação institucional.

## Recuperação

Fechar/reiniciar Jupyter não cancela jobs. Consulte os mesmos IDs. Reinício de
worker recupera entregas; dispatcher reenvia pendentes após janela60s. Tentativas
automáticas são limitadas1–4 e backoff10–60s. FAILED exige diagnóstico e retry-failed.
Consulte dashboard8088 por correlation_id/job_id/campaign_id e a aba Traces.
Não altere tabelas operacionais manualmente para continuar uma demonstração.

Reset09 só prepara/audita: [controlador externo](RESET_POC.md). O rebootstrap
sempre recria schema e serviços; empty é padrão, demo-ready também sem treinar.
