# Estrutura canônica V4

Migrations010–015 são aditivas no banco planejamento_db/schema planning.

| Contrato | Implementação |
|---|---|
| Fonte/linha/célula | academic_source_files, academic_reference_rows.payload |
| Dicionário da aplicação | academic_data_dictionary:31 entidades/175 campos |
| Curso/matriz/disciplina | views academic_course_identity, curriculum_identity, discipline_identity |
| Oferta/atividade | views academic_offer/offer_activity:70 ofertas/107 origens |
| Coorte | academic_cohort, com SYNTHETIC_ROLLING_COHORT |
| Demanda regular/adicional/total | cohort_regular_demand, discipline_nonregular_demand, discipline_total_demand |
| Simulação imutável | academic_simulation_snapshots, model_training_observations |
| De-para/unificação | academic_mapping, offer_unification_candidate; pendentes sem PRIME inventado |
| Treinamento | workbench_campaigns, workbench_models; checkpoint por identidade/versão |
| Aprovação/publicação | model_approval_requests, academic_deployments |
| Proposta | ai_proposals_v2, ai_proposal_offers_v2.payload; atividades filhas |

Dimensões são views sobre fontes imutáveis para evitar uma segunda cópia divergente.
UUIDs técnicos incluem arquivo/códigos originais e não representam IDs institucionais.
Ofertas preservam curso, grade, período, turno, disciplina e turma; coortes simuladas
incluem ingresso hipotético. Origem de cada atividade inclui SHA256/aba/linha/source_row_id.
Nenhuma exclusão automática de linhas repetidas;13 ficam em quarentena, afetando12 ofertas.

Capacidade homologada e grupos não estão disponíveis. O plano retorna REFERENCE_ONLY,
grupos vazios e pendência explícita. Não se transforma vagas desejadas em teto oficial.
Cabeçalho/ofertas originais são protegidos por trigger. Aprovação acadêmica e feedback
institucional ainda não são implementados; não confundir aprovação de modelo com esses estados.
