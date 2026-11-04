# ADR010 — Jornadas operacionais V2

04/11/2026. Decisão técnica da POC; não homologa regras acadêmicas.

A API recebe solicitações autenticadas e grava jobs antes de publicar no RabbitMQ.
O worker existente executa geração e treinamento; PostgreSQL é a fonte de verdade.
Migrations006/007 são aditivas. O transporte pode repetir/perder uma entrega sem
perder o pedido: dispatcher periódico, claim de envio, advisory lock por job,
heartbeat, checkpoint e tentativas limitadas permitem recuperação.

O ensaio inicial revelou tempestade de entregas duplicadas quando um no-op também
reagendava trabalho. Migration007 registra enqueued_at_utc; somente execução real
solicita despacho imediato. Reenvio pendente tem janela60s, heartbeat10s, dispatcher10s.
Concorrência máxima2 por campanha,2 processos no worker; cancelamento é cooperativo.
Falha definitiva aparece FAILED/evento; não há descarte silencioso em fila.

Modelo/run/SQL não compartilham transação distribuída. Versão nasce com tag
operation_job_id; retry recupera a versão já registrada e revalida seus bytes.
Run interrompida sem versão é marcada KILLED antes de nova tentativa. Pode haver
artefato órfão de tentativa interrompida; não é selecionado por inferência.
Proposta, linhas, atribuições e auditoria são uma transação. Manifest é posterior
e idempotente; retry após commit repara publicação sem gerar outra proposta.

Jornada01 conserva escrita DEMO legada. Jornada02 escreve exclusivamente via HTTP
API→worker→inferência→composição→PostgreSQL. Mesmo Idempotency-Key e payload
recuperam o mesmo job; alteração de payload retorna409. Nova chave é nova proposta.
Divisão N:N usa partição determinística de linhas entre seletores explícitos,
uma regra técnica de demonstração, sem decisão acadêmica implícita.

Campanhas usam modelos hi.demo.* em um experimento de domínio. Neste ensaio cada
identidade experimental treina sobre o mesmo snapshot sintético agregado; não
representa500 fontes ou cursos reais. Registro não promove nem cria servidor.
Inferência compartilhada mantém cache de até4 versões verificadas por processo.
Serviços dedicados legados continuam possíveis pelo fluxo já existente, sem
provisionamento automático em campanhas. Escolha institucional depende de SLO,
isolamento e medições de memória/latência, não apenas quantidade de modelos.

Governança V2 usa model_approval_requests para candidatos Ridge agregados, que não
possuem model_catalog acadêmico legado. model_deployments continua autoridade do
serving legado bundle2.0; os dois contratos não são intercambiáveis. A nova rota
APPROVED exige aprovação SQL e alias champion concordantes. Revisor vem de
OPERATOR_TOKEN separado de API_TOKEN; justificativa e versão são obrigatórias.
Falha de alias/commit bloqueia inferência aprovada até nova revisão/reconciliação.
Rollback exige versão anteriormente aprovada. Aprovação POC não publica no PRIME.

Pedido direto do usuário substitui a sugestão de duplicatas .update: uma entrada
por notebook; reiniciar preserva edições e atualização arquiva cópia exata fora
da lista antes de instalar a nova fonte. Backup de banco foi dispensado pelo
usuário durante montagem; backups existentes continuam protegidos pelo reset.
