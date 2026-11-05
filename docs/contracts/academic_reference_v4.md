# Referências acadêmicas V4 — contrato de importação

Migração 010, aditiva, no banco `planejamento_db`, schema `planning`.
Esta etapa é o staging acadêmico com chaves canônicas; ainda não é o conjunto
completo de dimensões/fatos de simulação nem o contrato de propostas v2.

| Objeto | Conteúdo / grão |
|---|---|
| academic_source_files | Arquivo original por SHA256, nome, tamanho e data de importação |
| academic_reference_rows | Uma linha física de DISCIPLINAS REGULARES, inclusive repetidas |
| academic_data_dictionary | Uma linha física da aba de campos da aplicação; não contém matrículas |
| v_academic_reference_activities | Atividade/divisão, valores planejados, vagas, proveniência e pendências |
| v_academic_reference_offers | Oferta identificada por chave acadêmica, com atividades filhas; sem somar estudantes |

UUIDs determinísticos identificam linhas por arquivo/aba/número. A chave da oferta
inclui ciclo, estabelecimento, escola, código de curso, grade, versão curricular,
turma, período, turno, disciplina e tipo. `2248` e `2348` permanecem distintos.
`Turma=U` não informa ingresso: `cohort_ingress` permanece nulo. IDs PRIME não
são inferidos. `mapping_status=UNMAPPED` significa ausência de de-para homologado.

`payload.source_cells` preserva endereço da célula, valor, fórmula original e tipo
para todas as células preenchidas da linha. Fórmulas não são calculadas; os valores
de fórmula, quando presentes, são os caches salvos no arquivo. Não executar macros,
links externos, consultas ou código VBA. As cópias de referência são somente leitura.

Os 107 registros foram conservados e agrupados em 70 chaves de oferta. Treze linhas
estão em quarentena: onze com valores não numéricos e duas ocorrências de PCS107A
com atividade/divisão repetida. A quarentena não apaga a origem nem autoriza deduplicação.
Não usar essas linhas como labels numéricos ou passar o gate de treino sem tratar a pendência.

P164/2248/período4 tem teoria Completa 41/45 e práticas P2-1 21/22 e P2-2 20/23
(planejados/vagas). Contagem única de referência: 41; não 82. Nenhum desses valores
é ocupação real, demanda eletiva ou resultado de IA.

**Diferença da SPEC:** o XLSX fornecido possui 31 entidades distintas e 175 campos.
O importador mantém todos e registra esperado=30/observado=31 no relatório.
Declarações de existência/disponibilidade são metadados do contrato; não comprovam
conexão ou carga de fonte institucional.

Persistência transacional, append-only pela identidade da fonte. Reimportar bytes
iguais e transformação igual não duplica; payload diferente com a mesma identidade
é rejeitado. Arquivo alterado recebe novo hash e conserva a versão anterior.
Aplicações devem escolher explicitamente a versão de fonte antes de simular.

PDFs funcional/arquitetura e diagnóstico ainda ausentes: nenhuma homologação funcional
nem conformidade C3/V4.4 integral foi atribuída a esta importação.
