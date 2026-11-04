# Code review e limpeza — 04/11/2026

A revisão V2 abrangeu API/contratos, worker e recuperação, treinamento/Registry,
inferência/cache, SQL/migrations/transações, lineage, autenticação/redação,
Jupyter/distribuição, Dockerfiles, scripts Windows/Linux, CI e documentação.
Inventário: [arquivos e hashes](../artifacts/reports/v2/repository-source-inventory.json).
As evidências históricas e os arquivos do usuário não foram tratados como lixo.

## Achados corrigidos

| Prioridade | Problema | Correção e verificação |
|---|---|---|
| Alta | Reset reiniciava RabbitMQ e uma fila vazia desaparecia, invalidando o plano | Parar somente os escritores na conferência; dois resets reais isolados e rebootstrap PASS |
| Alta | Notebook 09 rejeitava nomes de tabelas MLflow que contêm `secret` | Inventário apresenta identificadores como valores e somente contagem/hash; mantém filtro de segredos; teste específico |
| Alta | Jupyter não sobrescrevia relatório criado pelo UID de tools | Escrita atômica no diretório compartilhado; prova com os usuários reais e teste de arquivo somente leitura |
| Média | Grafo dizia VERIFIED quando relações eram truncadas | Contagem separada de relações; PARTIAL quando qualquer paginação trunca; regressão coberta |
| Média | Logs de inferência perdiam a correlação da geração | Propagação do correlation_id recebido, com fallback apenas para a jornada antiga |
| Média | Recuperação pesquisava somente a primeira página de versões | Percorrer todas as páginas do Registry; teste com duas páginas |
| Média | Campanha podia reutilizar experimento com localização direta S3 | Exigir experimento com proxy de artefatos antes de fit |
| Média | PowerShell e Python geravam credenciais com regras distintas | `init_env.py` único; testes de preservação, repetição e defaults não secretos |
| Média | Bootstrap Linux não liberava escrita dos diretórios para o UID Jupyter | Permissões explícitas nos diretórios compartilhados; overlay C3 respeitado |
| Baixa | Mudança de commit invalidava as camadas de dependências Docker | CODE_VERSION no final; Git instalado na camada de dependências |
| Baixa | Scripts históricos e imports redundantes dificultavam manutenção | Dez scripts removidos e 33 imports sem uso eliminados; lint F/E9 adicionado ao CI |

Também foram revisadas as correções V2 anteriores: claim persistente de envio
evita tempestade de mensagens; transação e chave idempotente evitam proposta
parcial/duplicada; recuperação após commit repara o manifest sem gerar outra
proposta; cancelamento e início usam a mesma ordem de locks.

## Limpeza aplicada

[Manifesto de exclusões](../artifacts/reports/v2/repository-cleanup.json) contém
caminho, SHA-256 anterior e substituto/justificativa para cada script removido.
Não foram encontradas cópias idênticas entre os arquivos não vazios mantidos.
Histórico Git permite consultar o código removido sem manter executáveis
obsoletos na árvore atual.

Os fluxos C3 por série e V2 por identidade experimental foram mantidos: têm
contratos, consumidores e provas diferentes. `publish_models.py`, bundle 2.0 e
rotas C3 ainda são usados pelos testes/CLI; não são uma segunda implementação
oculta da geração V2. As migrations anteriores são necessárias para instalar
bancos vazios e atualizar bancos existentes. Notebook-fonte, cópia editável e
notebook executado também têm responsabilidades diferentes.

## Validação e limites

78 testes unitários/integrados passaram na rodada principal da revisão, com
regressão adicional da escrita compartilhada na rodada final; lint F/E9 não
encontrou ocorrências. Testes reais cobriram reset isolado, SIGKILL do worker com
retomada de 30 treinos sem duplicar versões, falha MLflow/SQL, idempotência,
hashes S3, proposta N:N e preservação do ambiente principal. O aceite final V2
registra separadamente o commit, rebuild, notebooks e CI finais.

Esta revisão não certifica produção. Autenticação da POC usa tokens de serviço;
aprovação no Registry e PostgreSQL não é uma transação distribuída e a leitura
operacional bloqueia divergências. Modelos pickle exigem armazenamento e
identidade de treinamento confiáveis. A avaliação acadêmica continua pendente
de dados reais e homologação; as métricas de 500 treinos DEMO não medem 500
modelos carregados simultaneamente. Testes destrutivos usaram somente a stack
isolada. Não foi criado backup de banco, conforme orientação do usuário.

## Histórico da limpeza de 03/11/2026

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

Na revisão de03/11, a inicialização passou a distribuir somente a Jornada Completa e abrir
sua cópia editável. O volume templates foi removido da configuração; a recriação
do container aplica essa mudança, preservando o workspace.

Atualização04/11: a spec-correcoes v1.1 solicita um novo catálogo00–09, agora
distribuído sem sobrescrever edições. A limpeza acima descreve o estado histórico.
