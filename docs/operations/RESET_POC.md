# Reset total da POC — operação destrutiva

Não faz parte do quickstart, rebuild ou aceite comum. Notebook09 apenas apresenta
o comando de preview e lê o plano; factory-reset pode encerrar o próprio Jupyter.
Controlador Python no host, wrappers PowerShell/Bash, relatórios fora dos volumes
em `artifacts/reports/reset`. Nunca execute contra recursos compartilhados.

| Modo | Remove | Preserva |
|---|---|---|
| preview | Nada | Todos os dados; escreve somente plano |
| reset-data | Bancos exclusivos, objetos POC incluindo versões, vhost RabbitMQ | Volumes/imagens/configuração/workspace/backups externos |
| factory-reset | Containers e três volumes exclusivos validados | Fontes/.env/workspace/backups externos/imagens |

Preview consulta labels reais, consumidores dos volumes, endpoints, assinatura
Compose, tabelas/contagens/hashes e objetos/versionamento. Planos duram15min e
expiram em mudança de inventário/escopo/arquivos protegidos. Environment deve ser
poc e projeto/diretório estar na allowlist explícita. Nenhum force/yes/variávelCI
dispensa confirmação. Scope desconhecido ou volume compartilhado é rejeitado.

```powershell
python deployment/scripts/reset_poc.py preview --environment poc --project marista --mode factory-reset
```

Inspecione `<plan_id>.plan.json`. O comando abaixo é um modelo com placeholder,
não uma etapa de instalação. O programa solicita a frase digitada
`APAGAR TODOS OS DADOS DA POC MARISTA`:

```powershell
python deployment/scripts/reset_poc.py execute --environment poc --project marista --plan-id <UUID-DO-PLANO> --execute --reinitialize empty
python deployment/scripts/reset_poc.py status --environment poc --project marista --plan-id <UUID-DO-PLANO>
```

`empty`: schemas/serviços prontos sem dados sintéticos. `demo-ready`: catálogos e
snapshot seed, sem runs/modelos/propostas. Bootstrap cria objeto checks/compatibility
e pode criar Default vazio no MLflow; não são resíduos de treinamento.
O rebootstrap é obrigatório: quando omitido, `reinitialize` usa `empty`.
Não há treinamento ou promoção no rebootstrap.

Backup é decisão explícita antes do reset: use o procedimento existente de backup,
copie o resultado para armazenamento externo aos volumes da POC e valide a cópia.
O controlador recusa factory-reset se encontrar `backups/` no bucket, para impedir
perda silenciosa de backups anteriores. Não apaga arquivos gerados do workspace.

Falha parcial gera RESET_PARTIAL com passos concluídos. Não reutilize plano antigo;
diagnostique dependências e gere novo preview após recuperar serviços necessários.
O controlador falha fechado quando não consegue comprovar ownership ou inventário.
Escopo dinâmico com overlays não reconhecidos é recusado; revisão explícita da
allowlist é necessária antes de resetar esse cenário.
