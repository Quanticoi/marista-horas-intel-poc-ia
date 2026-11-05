# ADR-002 — Preservar contrato e adicionar proteção de proveniência

Revision 001 contém integralmente o SQL original da seção 8. Revision 002 acrescenta
somente funções/triggers: negar mutação de snapshot/histórico selado e negar UPDATE/
DELETE de previsões/sugestões originais. Nenhuma coluna/tabela do catálogo foi removida.
O seed insere histórico antes de selar no mesmo commit. Alterações humanas, fora
da implementação atual, deverão ser registradas separadamente na auditoria.

Adendo da seção 8/9 em spec.md enumera essas regras. O contrato SQL original permanece
preservado em [001_planning.sql](../../sql/ddl/001_planning.sql), com SHA256 fixado
na validação estática. A cópia histórica de especificação em `dev/` é local e não versionada.
Sem outbox/tabela de itens nesta baseline: payload e falhas por modelo ficam na
auditoria e error_summary. Recuperação de publish é explícita, sem garantia forte.
