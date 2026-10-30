# Revisão do repositório — 26/10/2026

Estratégia: Compose local; mesmos módulos/imagens em Kubernetes futuro.

## Removido ou isolado

- Dez scripts de instalação/operação específicos do Rancher local removidos.
- Cinco Dockerfiles especializados sem uso removidos; ficam aplicação e Jupyter.
- Quatro YAMLs de configuração sem consumidores removidos; ficam training, logging
  e environment, efetivamente utilizados. Não eram configurações ativas.
- Guia de deploy por namespace removido da documentação operacional.
- Export/migração/cleanup removidos após conclusão; validação diária não
  depende de restored.ok, hashes, backup original ou disponibilidade Kubernetes.
- Removidos também helpers de restore inicial, testes desses helpers, relatórios
  antigos redundantes, logs de port-forward e placeholders sem conteúdo.
- DNS Kubernetes fixo removido de defaults, dashboard e E2E; Compose não precisa
  simular aliases de namespaces.
- Gerador Helm não reescreve mais os oito notebooks antigos.
- README, instalação, comandos e operação atualizados para Compose.

## Preservado

Código de negócio, SQL/imutabilidade, testes, notebooks, workspace, .env, backups,
artefatos e histórico. Charts/manifestos e collector são referência futura, não
instalação de produção validada. ADRs e dev/spec.md preservam decisões anteriores;
as instruções de runtime local foram substituídas pela ADR 007.

## Próximos passos

1. Aplicar o fluxo C3: compose.ps1 build, migrate, start e validate.
   A execução dos containers novos ainda deve confirmar rede e provisionamento Docker.
2. Usar o notebook 09 e o serviço ingestion para a base sintética; templates foram atualizados,
   preservando cópias anteriores do workspace. Definir dataset institucional e critérios de qualidade.
3. Revisar candidatos, aprovar explicitamente as versões justificadas e executar
   publicar as APIs dedicadas e executar o E2E completo. Não há promoção automática.
4. Validar persistência e recuperação externa de bancos, RustFS, workspace e .env.
5. Publicar development no repo solicitado; ativar CI; staging após validação;
   main somente após homologação. Publicação não foi feita nesta sessão.
6. Antes de Kubernetes: registry, imagens imutáveis, secrets, storageClass,
   TLS/identidade, observabilidade, backup e pipeline no cluster alvo.

Limitações conhecidas: dashboard lê logs históricos; atuais via Compose. Dados
acadêmicos sintéticos e laboratório FRED/BLS não validam desempenho institucional.
Identificadores persistidos como pucpr-poc, pucpr-synthetic e nomes de modelos
foram mantidos para não quebrar URIs, artefatos e rastreabilidade. Antes de staging,
também definir tags imutáveis de imagem e CODE_VERSION vinculado ao commit Git.
