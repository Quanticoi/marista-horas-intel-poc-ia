# Fluxo de dados V4

1. **Referências:** três planilhas são lidas sem executar macros. A importação
   persiste 107 registros de origem, suas células/abas/linhas e SHA256. São 70
   ofertas; 13 registros em quarentena afetam 12 ofertas e permanecem rastreáveis.
2. **Simulação:** a estrutura acadêmica condiciona um histórico sintético seed 42,
   de 2022-1 a 2024-1, com entrada futura para 2024-2. O snapshot padrão contém
   285 observações: 227 históricas e 58 futuras. Planejamento não é usado como alvo real.
3. **SQL:** o Workbench consulta `planning.model_training_observations` por snapshot
   e prepara o escopo por curso. Regulares pertencem à coorte/ciclo; dependência e
   eletiva pertencem à oferta/ciclo. SQL e payload do snapshot são confrontados.
4. **Preparação:** o último ciclo histórico é avaliação; anteriores formam treino.
   Features incluem semestre, período e defasagens. Transformações são ajustadas
   somente no treino; alvos futuros não entram nas features.
5. **Treino:** três estimadores por modelo preveem regular, dependência e eletiva.
   Ridge é comparado com baseline; histórico insuficiente usa DummyRegressor com
   motivo. Avaliação regular usa uma observação por coorte/ciclo, evitando duplicação.
6. **Tracking:** cada nova campanha possui experimento próprio; runs representam
   campanha, lote e modelo. Métricas, perfil, dataset, código, assinatura e hashes
   acompanham versões estáveis por curso no Registry. Retomada explícita conserva a campanha.
7. **Governança:** revisão técnica e deploy explícitos habilitam versões. A inferência
   verifica aprovação SQL, alias, assinatura e checksum antes de usar os bytes persistidos.
8. **Geração:** a API cria job idempotente; o worker pede as três previsões por HTTP,
   compõe as categorias e grava cabeçalho/ofertas em transação. A publicação exige
   manifesto e job concluído. Nova chave cria outra proposta, preservando a anterior.
9. **Consumo:** a API consulta PostgreSQL; o notebook 09 pagina e verifica o contrato.
   O notebook 10 confronta proposta, inferências, modelos, runs, fontes e artefatos.

## Valores e decisões

Cada categoria separa previsão bruta e inteiro proposto (`max(0, ceil(previsão))`).
O total assume categorias disjuntas **somente na demonstração**. Ofertas em quarentena
mantêm demanda indisponível. Atividades são filhas da oferta, não população adicional.

Capacidade institucional permanece nula; modulação é `REFERENCE_ONLY`, com grupos
propostos vazios. Unificações aguardam dados/anuência. Não há regra fixa de capacidade
40 na V4, publicação PRIME ou revisão humana sobrescrita.

[Schema canônico](../contracts/canonical_schema_v4.md) · [Contrato HTTP](../contracts/academic_application_v2.md).
