# ADR 007 — Compose no desenvolvimento

Data: 2026-10-26. Decisão autorizada pelo usuário.

**Situação atual:** migração concluída, cinco namespaces/PVs antigos removidos.
As condições de export/remoção abaixo registram o procedimento já realizado.
Os scripts temporários desse procedimento foram excluídos. Validação diária verifica
serviços e acessos; contagens/hash do backup foram checks específicos da migração.

Compose passa a ser o runtime de desenvolvimento, substituindo a exigência anterior
de Kubernetes local. Helm continua para staging/produção. Código e Dockerfiles
compartilhados; endpoints e credenciais configuráveis. RustFS permanece.

Preservar bancos, versões S3, workspace e logs antes de remover os cinco namespaces
da POC. Remoção condicionada à restauração e aos testes no Docker. Não remover
recursos de sistema nem dados de outros projetos. Manter backup local ignorado
pelo Git. Não alterar conteúdo ou executar notebooks durante a migração.

Pipeline verifica pip check, saúde, autenticação/conectividade de dependências,
testes unitários/integração, contagens do MLflow e leitura de artefatos.
Logs atuais via Compose; dashboard retém consultas de negócio, conexões e logs
históricos importados. Coletor Kubernetes não executa no Compose.

Fluxo de branches permanece development → staging → main após homologação.
