# Linux

Docker Engine, plugin Compose, Git e Python 3.11+ para os utilitários de validação.
O script abaixo prepara as credenciais ausentes, os diretórios e suas permissões,
constrói as imagens, inicializa bancos/bucket e executa a jornada. Preserve o
`.env` de qualquer ambiente que já tenha volumes.

```bash
sh deployment/scripts/journey.sh rebuild
make test
```

`init_env.py` é a única implementação de geração de credenciais, também usada
pelo PowerShell. O servidor MLflow migra seu próprio schema antes de liberar
o listener. Rebuild preserva os volumes. Para publicação C3 opcional, execute
`python deployment/scripts/publish_models.py --model CHAVE` após aprovação e depois
`docker compose -f compose.yaml -f .runtime/models.compose.json up -d --wait`.
[Fluxo completo](../operations/C3_TRAINING.md).
