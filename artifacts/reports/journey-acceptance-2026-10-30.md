# Aceite técnico executado — 30/10/2026

Runtime: Docker Desktop, contexto `desktop-linux`, projeto Compose `marista`.
Sem Rancher/Kubernetes, conforme decisão reafirmada pelo usuário. Serviços da
solução executados exclusivamente em containers. Dados sintéticos, seed 42.

Conferência final: 11 containers `healthy`; 12 células de código do notebook
executadas sem saída de erro. SHA256 do notebook executado:
`dea6f72af9fc1738abce64a42cc8f529c2a77496fa156448d698d4fa8c11963f`.

## Resultado real

- `compose.ps1 rebuild`: exit 0 após correções; imagens construídas, bancos,
  migrations, bucket/seed, readiness, pip check, notebook e integração executados.
- `compose.ps1 acceptance`: exit 0. Sete testes antes, sete após restart do MLflow,
  sete após rebuild, conferindo a **mesma** execução, modelo e proposta.
- `compose.ps1 test`: exit 0. **37 testes** unitários/integração e **19 checks HTTP**
  de interfaces, autenticação e rejeição de acessos anônimos passaram.
- `python dev/generate_compose.py --check`: manifesto e gerador semanticamente iguais.
- Parser PowerShell: PASS. Evidências da jornada verificadas contra valores de
  segredos do `.env`, sem ocorrências.

## Identificadores

| Evidência | Valor |
|---|---|
| execution_id / correlation_id / proposta | `a741d0dd-d1ed-41eb-91d1-d5194c5fb692` |
| experimento | `4`, `planilha-turmas-proxy-v1` |
| run_id | `ad2530361ab14f7d87017c21d11958a1` |
| modelo e versão | `planilha-turmas-demo`, `3` |
| URI registrada | `models:/planilha-turmas-demo/3` |
| artefato MLflow 3 | `models:/m-1717e4e5a7d540de8ecd8aed5e40a049` |
| snapshot | `fb931e1e-43d0-5ff8-938c-0d2ba4a68794` |
| SHA256 extração | `5fc39eeeead59aa48813182e6a93d2308a4a9243655501f17d09a981c6c66a56` |
| linhas SQL | 1.050 (350 históricos × 3 disciplinas) |
| treino / avaliação / proposta | 960 / 90 / 90 linhas |
| MAE / RMSE | 3,7586306583 / 4,9142272797 estudantes (DEMO) |
| linhas persistidas / retornadas API | 90 / 90 |

[Abrir run no MLflow](http://127.0.0.1:5000/#/experiments/4/runs/ad2530361ab14f7d87017c21d11958a1).
Consulta autenticada: `GET /v1/proposals/a741d0dd-d1ed-41eb-91d1-d5194c5fb692`.
As versões 1 e 2, geradas nas verificações anteriores desta sessão, foram preservadas.

## Matriz A–L

| Critério | Evidência / resultado |
|---|---|
| A — serviços disponíveis | PASS: readiness Compose, dependências, pip check e HTTP; runtime adaptado para Docker por instrução explícita |
| B — kernel novo, Run All | PASS: nbclient executou o notebook inteiro com kernel `pucpr`, sem allow_errors |
| C — leitura SQL | PASS: extração parametrizada, PostgreSQL, snapshot/hash e 1.050 linhas exibidos |
| D — MLflow indisponível | PASS: porta fechada dentro do container, bloqueio antes do fit, sem `mlruns`/SQLite |
| E — treino/métricas reais | PASS: Ridge fit/predict, MAE/RMSE calculados; transformação ajustada somente no treino |
| F — tracking/artefatos | PASS por SDK e HTTP: parâmetros/métricas/tags, referências, modelo e evidência recuperados; **inspeção visual da UI pendente** |
| G — reinício MLflow | PASS: mesma run, modelo, bytes e proposta após restart |
| H — reload | PASS: modelo removido da memória de treino, download por versão, nova carga no serviço de inferência |
| I — versão e artefato | PASS: vínculo de run/versão e SHA256 dos bytes do proxy iguais aos do RustFS |
| J — proposta e API | PASS: 90 linhas em PostgreSQL, reconciliação de chaves/quantidades/previsões, eventos no dashboard |
| K — idempotência | PASS: payload igual retorna geração existente; diferente rejeitado; FK inválida reverte a transação |
| L — rebuild | PASS: mesma execução/versão/proposta recuperada após build, migrations e recriação dos serviços |

## Arquivos de evidência

- `01_jornada_completa_planilha_turmas.executed.ipynb`: células, tabelas, métricas e links.
- `journey-latest.json`: resumo da execução identificada acima.
- `journey-junit.xml`: sete testes da jornada antes do reinício.
- `journey-after-restart.xml` e `journey-after-rebuild.xml`: sete testes em cada fase.
- `compose-junit.xml`: suíte geral, 37 testes.
- `access-check.json`: 19 checks de acesso.

O resumo também foi enviado ao Artifact Store como artefato `evidence` da run.
Logs atuais em `data/compose-logs`, consultáveis pelo mesmo correlation_id.

## Correções e limites

O primeiro rebuild falhou porque `JUPYTER_TOKEN` estava vazio. O valor foi
recuperado do container existente sem ser exibido, preservando as demais credenciais.
A primeira execução completa do notebook passou, mas dois testes seguintes falharam
porque a injeção de indisponibilidade alterava globalmente o SDK/ambiente MLflow.
A fixture agora restaura ambos, e a suíte completa passou após a correção.

O tratamento de falha de etapa foi ajustado para preservar o diagnóstico original
mesmo quando o tracking estiver indisponível. A instalação nova executa a jornada
antes dos testes que dependem de seu relatório. O gerador Compose foi sincronizado
com SQL, relatórios e logs da jornada para evitar regressão em futuras gerações.

Não foi possível realizar a inspeção visual da UI: a ferramenta retornou
`The browser access host is unavailable`. Os endpoints HTTP e os dados consumidos
pela interface foram verificados, mas não se declara inspeção visual concluída.
Não foram executadas instalação em volumes vazios nem a variante Bash/Linux nesta
sessão; o teste real foi de rebuild sobre os volumes existentes no Windows.

Fonte REAL, regras definitivas de modulação/MER, homologação funcional, promoção
operacional e produção não estão aprovadas nem demonstradas. A proposta permanece
DRAFT e não há alias operacional promovido por esta jornada. Não houve commit/push.
Warnings de depreciação de botocore/Starlette não impediram os testes.
