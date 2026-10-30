# Fluxo e semântica

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
