# Histórico compacto

Ler primeiro `state.md`. `events.tsv` é append-only: data, ação, resultado/evidência.
Registrar decisões, alterações, checks e bloqueios em uma linha por lote; sem transcrições,
credenciais ou saídas extensas. Código e diffs ficam no Git; evidências em artifacts/reports.
Fluxo autorizado: development → staging após validação → main após homologação do usuário.
