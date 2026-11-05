# Cobertura funcional V4 e limites V4.4

As provas técnicas usam estrutura de planejamento e histórico sintético. Aprovação
de modelo para DEMO não substitui validação acadêmica, matrícula oficial ou decisão
do coordenador. A tabela abaixo descreve o estado implementado, não uma homologação.

| Referência | Demonstrado | Limite / pendência |
|---|---|---|
| RF020–026 | Coorte sintética, regular comum por coorte/ciclo e adicionais por disciplina | Ingresso hipotético e fonte declarada; matrícula oficial ausente |
| RGN023 / US028 | Estado inicial `DRAFT_PENDING_COORDINATOR` | Gate acadêmico de matriz não implementado; sem docentes/horários/salas |
| RF040–047 | Modulação `REFERENCE_ONLY`, valores de referência preservados | Capacidade institucional ausente; grupos propostos vazios; nenhum teto 40 inventado |
| RF117–125 | Candidatos e pendências de unificação rastreáveis | Sem de-para PRIME, anuência ou efetivação automática |
| RF155–159 / US005–006 | Snapshot SQL versionado, leitura e proveniência | Sem conector institucional ou escrita PRIME |
| RF195–199 / US016 | Logs, Traces e auditoria SQL/Registry/RustFS | Perfis institucionais e exportação formal não homologados |
| RF204–206 / US017 | Originais imutáveis, revisões não sobrescritas, `feedback_cycles_count=0` | Sem ingestão de feedback humano validado para treino |
| US022 | Sem ensaio funcional dedicado | Escopo requer definição pelos responsáveis |

S01 preserva P164 como uma oferta e três atividades; S02 mantém regulares comuns
à coorte de CiberSegurança e adicionais específicos. S03 retorna
`PENDING_DATA/PENDING_APPROVAL`; não resolve ausência de dados por suposição.

Treinamento ocorre no Workbench. Geração/persistência pertencem ao worker; consulta
da aplicação usa HTTP v2. [Fontes examinadas](V4_SOURCE_REVIEW.md),
[decisão V4](../adr/012-workbench-academic-v4.md) e
[aceite técnico](../../artifacts/reports/v4/acceptance-v4.md) fornecem as evidências.
