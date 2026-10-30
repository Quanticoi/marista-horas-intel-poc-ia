# Fluxo de branches

Repositório: https://github.com/Quanticoi/marista-horas-intel-poc-ia (público).

- `development`: implementação e evolução da POC; destino do primeiro envio de código.
- `staging`: reservada para validar uma entrega quando o trabalho em development
  estiver finalizado. Inicialmente aponta apenas para o commit-base vazio.
- `main`: reservada para uma eventual versão homologada. Inicialmente contém
  apenas a mesma base vazia; pode permanecer sem uso.

Não há promoção automática entre branches. Quando solicitada, a promoção será
feita por PR de `development` para `staging`; depois, se necessário e autorizado,
de `staging` para `main`. A criação das branches não implica homologação.

O primeiro envio inclui código, notebooks sem saídas, documentação, manifests,
testes e evidências DEMO revisadas. `.env`, workspace, backups, volumes, caches
e logs locais não são publicados. Nunca use `git add -f .env`.

O workflow `.github/workflows/compose.yml` valida o projeto em containers efêmeros
no runner do GitHub, com credenciais temporárias. Não faz deploy na máquina local.
O relatório de execução local não substitui o resultado desse workflow.
