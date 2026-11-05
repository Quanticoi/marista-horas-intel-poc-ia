# 012 — Treinamento local e inferência operacional V4

O C3 exige que o custo científico pertença ao Workbench. Campanhas V4 executam fit,
transformações e avaliação no container Jupyter, com limite de concorrência1..2,
checkpoints PostgreSQL e runs pai/lote/modelo no MLflow. O worker operacional recusa
jobs de treinamento; o endpoint legado retorna410. Consultas históricas continuam.

Os três modelos por curso têm saída regular/dependência/eletiva; regulares usam somente
features comuns à coorte. Avaliação temporal sintética não constitui qualidade real.
A promoção é explícita e usa a reconciliação RECONCILING existente. Deploy e residência
são estados diferentes. O serviço existente de inferência atende V4 com cache próprio
limitado, checksum/assinatura antes de carregar e aprovação a cada chamada.

API/worker executam somente inferência e composição. O contrato V2 preserva origens e
atividades, mantém quarentena e não inventa capacidade/anuência. Notebook09 consome
HTTP paginado autenticado; não acessa SQL ou SDKs de storage/tracking para sua tabela.
Não há nova stack de serviços, binários duplicados ou schema MLflow recriado pela aplicação.

## Adendo — campanha nova e reset seletivo (05/11/2026)

Por solicitação do usuário, NEW cria um experimento próprio para cada campanha,
com data UTC e UUID. RESUME conserva o checkpoint e o experimento da campanha
existente; não é modo implícito. Novas versões não sobrescrevem versões anteriores.

O modo reset-experiments limpa MLflow, objetos derivados no RustFS e resultados
operacionais, preservando cinco tabelas de origem acadêmica/sintética SQL. Contagens
e hashes são comparados antes/depois. A execução permanece no controlador externo,
com plano e confirmação; o notebook orienta e não apaga durante Run All.
