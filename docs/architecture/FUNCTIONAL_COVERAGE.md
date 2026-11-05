# Responsabilidades e cobertura V3/V4.4

## Atualização V4 — prevalece sobre o quadro histórico abaixo

RF020–026: estrutura de coorte/regular/adicionais implementada com fontes e hipóteses
sintéticas explícitas. Não há histórico oficial fornecido. RGN023: proposta inicial
DRAFT_PENDING_COORDINATOR, sem docentes/horários/salas; gate acadêmico institucional
não implementado. RF040–047: capacidade oficial ausente, modulação REFERENCE_ONLY;
não aplicar teto40 nem converter vagas desejadas em regra. RF117–125: candidatos de
unificação pendentes, sem efetivação ou anuência inferida. RF204–206: original imutável;
feedback_cycles_count=0, sem ingestão de revisão intermediária para treino.

Workbench faz fit local; worker somente inferência/persistência; API V2 entrega70 ofertas
e107 atividades de origem. Foram testados cenários P164 e CiberSegurança. S03 permanece
PENDING_DATA/PENDING_APPROVAL. Essas provas não homologam as regras V4.4 completas.
Ver [fontes examinadas](V4_SOURCE_REVIEW.md) e [decisão V4](../adr/012-workbench-academic-v4.md).

## Quadro histórico V3

Fontes e URLs consultadas em [diagnóstico](../../artifacts/reports/correcoes-fase-a-2026-11-04.md).
Não se afirma homologação das237 regras. O payload é provisório.

| Referência | IA/POC | Aplicação-alvo | Resultado |
|---|---|---|---|
| RGN001/US027 | Sugestão DRAFT | Decisão/edição do coordenador | Parcial DEMO |
| RGN002/RF010 | Dados sintéticos de vários cursos | Integração de ofertas | NOT_EVALUATED |
| RGN003/RF021–025/US029–030 | Previsão agregada | Quantidades PRIME e categorias/origens | NOT_EVALUATED |
| RGN023/US028 | Sem docente na primeira representação | Gate humano da matriz | NOT_EVALUATED |
| RF008–009 | Docente/horário/sala ausentes | Matriz/turno/oferta regular | Parcial DEMO |
| RF020/US026 | Curso/período existentes | Coorte de ingresso | NOT_EVALUATED |
| RF040–047/US033–034 | Ceil por capacidade40 provisória | Matriz/unificação/modulação homologada | NOT_EVALUATED |
| RF117–125 | Nenhuma unificação efetivada | Elegibilidade/manifestação/GQA | NOT_EVALUATED |
| RF155–159/US005–006 | SQL temporal/snapshot sintético | Hub/fontes oficiais, sem escrita PRIME | Parcial técnico |
| RF195–199/US016 | Logs/traces/auditoria append-only | Perfis/escopos/exportação formal | Parcial técnico |
| RF204–206/US017 | Original imutável | Revisão humana e feedback validado | Parcial técnico |
| US022 | Sem ensaio funcional dedicado | Validar escopo com responsáveis | NOT_EVALUATED |

V2 preserva a representação sem docente/horário/sala. API/worker agora geram
proposta DRAFT e persistem atomicamente; aprovação técnica de versão de modelo
não é o gate humano institucional da matriz acadêmica. As classificações
NOT_EVALUATED da tabela permanecem válidas.

V3: Workbench submete/experimenta; jobs treinam; MLflow mantém Tracking/Registry; Object Storage recebe
artefatos; inferência recarrega versão; worker da aplicação orquestra e persiste;
Hub medeia fontes/publicação aprovada. POC mantém adaptador Jupyter de escrita
DRAFT na jornada01 por compatibilidade. O aceite V2 usa notebook02 como cliente
HTTP; API/worker possuem a responsabilidade operacional de geração/persistência.
`src/persistence/journey.py` e `src/api/proposal_contract.py` podem ser utilizados
pelo worker, sem dependência de célula ou objeto de notebook.
