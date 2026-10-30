> Jornada atual (30/10/2026): veja [JOURNEY.md](JOURNEY.md). Notebook principal 01_jornada_completa_planilha_turmas; Docker Compose; eventos atuais no dashboard. Resultados reais e pendencias em history/state.md; validacoes historicas abaixo nao substituem o aceite atual.

# Aceitação pendente

Migração validada: 19 testes, 39 runs, 36 modelos/versões e 124 objetos.
Isso não homologa desempenho de modelos nem produção.

1. Após alterações: compose.ps1 build, migrate, start e validate.
2. Validar uma série pelo [fluxo C3](C3_TRAINING.md); depois revisar, aprovar e publicar as 30 versões apenas se justificadas.
3. docker compose run --rm tools e2e; registrar evidência real.
4. Conferir persistência após reinícios.
5. Validar backup/restore isolado e recuperação externa de objetos/workspace.
6. Revisar autenticação, idempotência, logs e limites.
7. Publicar development; staging após validação; main após homologação.

O notebook 09 implementa o fluxo C3; cópias anteriores no workspace continuam sob controle do usuário.
