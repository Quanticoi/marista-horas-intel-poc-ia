# Revisão da estrutura — 03/11/2026

A organização acompanha a jornada SQL → treinamento → MLflow → inferência →
Planilha Turmas → API, com os serviços Docker Compose e seus fluxos auxiliares.

## Removido

- Pastas locais vazias data/raw, bronze, silver, gold, samples, snapshots e public:
  o runtime não as usa; histórico e snapshots ficam em PostgreSQL/RustFS.
- Charts Helm, manifests Kubernetes, valores por ambiente e gerador desses arquivos.
- Coletor Kubernetes e sua configuração/dependência; dashboard lê diretamente os
  eventos JSONL do ambiente Compose.
- Dockerfiles/directórios especializados vazios e diretórios SQL sem consumidores.
- Gerador e saídas do laboratório público macroeconômico, fora da jornada acadêmica.
- Ambiente virtual antigo, cópias temporárias de validação e scripts de inspeção
  descartáveis, sem referência no runtime atual.
- Dez notebooks antigos distribuídos. No workspace, suas cópias e um notebook
  executado foram arquivados fora do Jupyter antes da remoção.

## Preservado

- Notebook principal, módulos Python utilizados, consultas SQL e migrations.
- Serviços Compose, imagens da aplicação/Jupyter, testes e scripts operacionais.
- PostgreSQL, RustFS e RabbitMQ com seus volumes; nenhuma operação nos volumes.
- .env, backups originais e arquivo local de recuperação dos notebooks removidos.
- data/compose-logs, relatórios da jornada/C3 e dados de rastreabilidade.
- Edições do notebook principal, arquivos pessoais Untitled e checkpoints.
- Histórico Git, decisões arquiteturais e especificações de referência usadas
  para conferir os contratos SQL.

O inventário de remoção, com caminhos e contagens, está em
[cleanup-2026-11-03.json](../artifacts/reports/cleanup-2026-11-03.json).

A inicialização do Jupyter passa a distribuir somente a Jornada Completa e abrir
sua cópia editável. O volume templates foi removido da configuração; a recriação
do container aplica essa mudança, preservando o workspace.
