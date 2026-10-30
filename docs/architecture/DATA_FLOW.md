# Fluxo dos dados

## Jornada principal: proposta de Planilha Turmas

1. `tools seed` produz dados sintéticos com semente 42 e persiste catálogo,
   histórico e snapshot selado no schema `planning`. O padrão contém 350
   observações de 30 séries semestrais; Parquet e manifesto ficam no RustFS.
2. O notebook abre SQL como `planning_readonly`. A consulta
   `sql/queries/journey_history.sql` recebe snapshot, ciclo e curso, aplica corte
   temporal e relaciona cada período às suas três disciplinas. No escopo completo,
   retorna 1.050 linhas. Nulos, duplicidades e chaves necessárias são verificados.
3. Os semestres anteriores ao último histórico formam o treino (960 linhas).
   O último semestre avalia o modelo (90 linhas). A entrada da proposta contém
   chaves acadêmicas e semestre futuro, sem a variável-alvo (90 linhas).
4. One-hot das chaves e padronização temporal são ajustados somente no treino.
   O Ridge prevê total de estudantes. MAE/RMSE são calculados no conjunto reservado.
5. O MLflow recebe referências SQL/CSV, hashes, parâmetros, métricas e o pipeline
   ajustado. O proxy grava os artefatos no RustFS; o Registry associa uma versão
   à run. O modelo é recarregado pela versão explícita no notebook e na inferência.
6. Regra provisória: estudantes propostos = max(0, teto(previsão)); turmas =
   teto(estudantes/capacidade), com capacidade 40. Cada disciplina recebe a demanda
   integral de seu período. Zero demanda gera zero turmas nesse contrato DRAFT.
7. A transação grava `proposal_generations`, `proposal_lines` e auditoria. O UUID
   da execução é a chave idempotente; payload diferente com o mesmo UUID é rejeitado.
   Novo Run All cria uma geração nova e preserva as anteriores.
8. A API lê essas tabelas. O notebook reconcilia chaves, previsões, quantidades,
   run e versão, e salva evidências no workspace, nos relatórios e no MLflow.

O hash da extração identifica as linhas consultadas; o hash/versão da SQL e o
hash de código documentam como foram obtidas e processadas. O `execution_id`
acompanha a run, a versão, a proposta e os eventos como `correlation_id`.

A regra de composição é demonstrativa e exige validação funcional. O campo de
ajuste humano fica separado dos valores calculados. As métricas deste dataset
sintético não representam qualidade em dados institucionais.

O fluxo abaixo mantém um contrato de previsão por série e publicação operacional
próprio. Suas regras de distribuição não substituem a composição DRAFT acima.
## Fluxo complementar: séries acadêmicas e modelos publicados

1. Gerador determinístico produz 3 campi × 5 cursos × 2 períodos. São 12 semestres
   por série, com uma lacuna e uma série nova de 3 pontos: 350 linhas na configuração padrão.
2. Raw, Bronze, Silver e Gold são Parquet por snapshot. Nesta baseline sintética,
   os registros já chegam tipados/canônicos; camadas preservam as mesmas colunas,
   passando por validação de chaves, referências, ordenação, contagens e corte temporal.
   Não há imputação de períodos ausentes. O serviço ingestion recebe JSON no mesmo contrato
   agregado e valida antes de persistir; conectores institucionais ainda não estão implementados.
3. UUID do snapshot deriva do conteúdo, configuração (incluindo ciclo/data de corte) e versão do schema. Manifesto
   contém hashes de cada camada. O banco registra Gold; o manifesto referencia as demais.
   Uploads existentes são comparados antes de reutilização; versionamento do bucket é habilitado.
4. Treino valida hash do manifesto registrado no banco, hash do Gold, proveniência e contagem de linhas. Backtest expansivo usa apenas histórico
   anterior a cada alvo; compara sazonal, Ridge e RandomForest quando há amostra.
   Pouco histórico usa baseline explícito. O binário guarda o estimador ajustado e a lógica
   de previsão; bundle.json guarda proveniência e SHA256 de cada arquivo. O treinamento
   baixa o binário do RustFS e compara previsões antes de registrar a versão.
5. MLflow recebe tags snapshot/model_key/code_version/config_hash, métricas e versão
   candidata. Promoção exige operador e razão, grava DB/auditoria e ajusta champion.
6. Publicação cria um servidor/API por modelo aprovado. Ele carrega o binário verificado
   na inicialização, confere versão/URI/alias e proveniência em cada chamada e não chama fit.
   Cache limitado a duas entradas por processo, chave URI+versão+checksum. Nova aprovação
   exige republicação; divergência de alias ou aprovação revogada bloqueia a execução.
   Versões antigas apenas JSON continuam no histórico, mas não são publicáveis neste contrato.
7. Cada disciplina do período recebe a projeção integral do grupo, com divisão
   sintética 85% regulares, 10% dependência e restante eletivas. Turmas = teto(total/40),
   mínimo 1 para cumprir DDL. **Não são matrículas reais nem solver de ensalamento.**
8. Avaliação pós-ciclo usa actuals do semestre alvo em snapshot posterior selado.
   Na ausência deles retorna PENDING_ACTUALS. Não fabrica resultado de qualidade.

Unicidade (job,model) e (prediction,discipline) protege retries. Locks PostgreSQL
serializam jobs e promoções por modelo. Commit antes de publish tem recuperação
explícita `docker compose run --rm tools recover`, não outbox: não se promete entrega automática após falha.
