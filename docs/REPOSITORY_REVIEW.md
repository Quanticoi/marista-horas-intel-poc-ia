# Revisão do repositório e documentação V4

Revisão de 05/11/2026, confrontando documentação com Compose, scripts, módulos de
treinamento/serving/reset, SQL e catálogo real dos notebooks.

| Achado | Adequação |
|---|---|
| Guias ainda ensinavam treino pelo worker e `tools train` | Treino exclusivo no Workbench; rotas operacionais legadas desativadas |
| MLflow documentado com upload direto e `--no-serve-artifacts` | Proxy MLflow, metadados PostgreSQL e verificação de bytes RustFS |
| Capacidade 40, divisão fixa e 90 linhas descritas como fluxo atual | Contrato v2 com 70 ofertas/107 origens, categorias e pendências explícitas |
| Notebook único/00–09 misturados à V4 | Catálogo 00–11 e fluxo de contexto 05→08→09→10 |
| API por modelo descrita como padrão atual | Serving compartilhado, PRELOAD/LAZY, elegibilidade e cache limitado |
| Rebuild descrito como treinamento automático | Bootstrap separado da ciência e das decisões de aprovação |
| Roteiros V2/V3 no diretório de operação atual | Manuais em `docs/archive/`, links corrigidos e status histórico explícito |
| ADRs anteriores apresentadas como decisão vigente | ADR 012 como referência atual; textos anteriores preservados e identificados |
| Experimento/chave fixos dificultavam distinguir novos ensaios | NEW cria experimento próprio; RESUME exige chave existente |
| Reset do notebook confundido com limpeza efetiva | Preview/execute externos e modo seletivo com origem SQL preservada por hash |

O README foi reorganizado por objetivo, início rápido, arquitetura, acessos,
jornada, persistência e evidências. O índice `docs/README.md` aponta para os guias
vigentes. Tutoriais repetidos foram reduzidos a responsabilidades específicas.

Scripts geradores/executores antigos substituídos na V4 foram retirados; migrations,
contratos legados e notebooks em `notebooks/legacy/` permanecem para compatibilidade.
`dev/` e `history/` são locais e ignorados. Não foram apagados volumes, credenciais
ou edições do usuário durante esta revisão. O reset destrutivo foi testado somente
na stack isolada.

O [relatório dos ajustes](../artifacts/reports/v4-adjustments/README.md) identifica
testes, verificação de links, limites e hashes. O
[inventário anterior](../artifacts/reports/v4/repository-source-inventory.json)
é um checkpoint anterior à revisão documental; não representa os novos bytes.
