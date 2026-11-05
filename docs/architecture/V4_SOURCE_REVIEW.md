# Conferência das fontes V4

Documentos fornecidos em `dev/`, mantidos localmente. Nomes efetivos e SHA256
constam em `artifacts/reports/v4/source_inventory.json`. Os sufixos de download
`(1)`/`(2)` e espaços duplicados não definem a versão do conteúdo; hashes continuam
sendo conferidos e cópias diferentes permanecem ambíguas.

Foram lidos os três diagramas V3 de uma página, com renderização e inspeção visual,
e as páginas funcionais relevantes do documento V4.4 (92 páginas): 15, 18, 20,
27–29, 40–41, 60, 73, 75 e 80. Não se declara revisão integral das 92 páginas.

| Fonte / páginas | Regra confirmada | Consequência na implementação |
|---|---|---|
| Componentes, Containers e Sequência V3, p.1 | Workbench treina; MLflow registra; inferência carrega modelo aprovado; worker orquestra e persiste | Treino V4 deve executar localmente no container Jupyter; substituição do fluxo legado ainda pendente |
| V4.4 p.18, RF020–026 | Coorte por ingresso, regulares separados dos adicionais | Simulação declara ingresso hipotético e mantém fatos separados; nenhuma ligação PRIME é inventada |
| V4.4 p.15 e 75, RGN023 | Validar matriz antes das etapas seguintes | Não simular aprovação acadêmica nem liberar automaticamente ofertas especiais |
| V4.4 p.20, RF040–048 | Unificação precede modulação; capacidade vem da matriz | `reference_seats` não vira capacidade homologada; grupos atuais são referência, não modulação efetivada |
| V4.4 p.27–29, RF117–125 | Código PRIME/campus/escola/turno, concordâncias e GQA | Candidato sem dados/anuência fica pendente, ofertas originais separadas |
| V4.4 p.40–41, RF204–206 | Preservar original e aprender somente com resultado validado; restrições não são calibráveis | Snapshots imutáveis; feedback_cycles_count=0; sem feedback intermediário no treinamento |

O diagnóstico Markdown citado na SPEC não foi localizado. Este documento é uma
conferência nova do código/fontes, **não** uma substituição daquele arquivo.

## Simulação implementada (parcial da fase B)

O manifesto usa a estrutura importada, exclui 12 ofertas com 13 linhas em quarentena
e conserva todas as 70 ofertas na referência. Produz 285 observações: 227 históricas
e 58 futuras. Janela 2022-1..2024-1, alvo 2024-2. Cada currículo só recebe observações
a partir da data presente em seu nome, usada como limite hipotético, não como vigência oficial.

Cada ciclo representa uma coorte sintética por curso/grade/turno/turma/ingresso
hipotético. Ingresso é inferido apenas para o cenário sintético a partir do período;
não altera a referência original, cujo ingresso continua desconhecido. Intake 35–70
antes do fator de cenário, retenção/progressão, reprovação/retomada e preferências
são hipóteses configuradas, nunca ocupação real nem planejamento usado como label.
Categorias são disjuntas por hipótese declarada. Eletiva sem elegibilidade confirmada
assume zero no cenário, marcado como hipótese, não como quantidade factual conhecida.

Seed42 e cenário baseline geram o mesmo hash lógico; growth, decline, high_dependency
e elective_pressure são opções explícitas. Histórico não depende do target futuro.
Alterar valores planejados não altera os rótulos sintéticos. Ainda faltam estratégia
de cold start executada pelo modelo, dimensões canônicas completas, executor/MLflow,
serving V4, contrato v2 e simulador HTTP final.

Migrações 011/012: snapshots e observações persistem no PostgreSQL; views separam
regulares por coorte, adicionais por disciplina e total por oferta. Triggers bloqueiam
UPDATE/DELETE das cinco tabelas de referência/simulação. Nenhuma tabela do MLflow é alterada.
