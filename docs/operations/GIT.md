# Repositório e branches

Destino: [Quanticoi/marista-horas-intel-poc-ia](https://github.com/Quanticoi/marista-horas-intel-poc-ia).

- `development`: implementação e evolução da POC.
- `staging`: validação de uma entrega selecionada.
- `main`: eventual versão homologada.

Não há promoção automática entre branches. Um commit local não comprova publicação
no GitHub; o relatório da entrega informa separadamente commit e push.

`.env`, `dev/`, `history/`, `workspace/`, caches, backups e arquivos de referência
locais são ignorados. Os fontes dos notebooks não carregam saídas; evidências
executadas ficam identificadas em `artifacts/reports`. Não versionar credenciais.

O workflow Compose executa em containers do runner. O pacote de referências é
externo ao Git; sem ele, a etapa E2E V4 deve indicar SOURCE_MISSING/NOT_EXECUTED.
Evidência local não substitui resultado de CI remota.
