# Linux

Docker Engine e plugin Compose. Sem Rancher/kubectl/Helm no desenvolvimento.
Prepare .env com valores aleatórios para cada chave de .env.example; preserve
as credenciais de volumes existentes. Crie workspace/notebooks, data/compose-logs
 e artifacts/reports com permissão para os usuários das imagens.

```bash
docker compose build mlflow jupyter
docker compose run --rm --no-deps --entrypoint chown volume-tools 10001:10001 /restore/rustfs
docker compose up -d --wait postgres rustfs rabbitmq
docker compose run --rm tools bootstrap
docker compose run --rm tools migrate
docker compose run --rm tools buckets
docker compose run --rm tools seed
docker compose up -d --wait --wait-timeout 300
make test
```

Atualização C3: acrescentar INGESTION_TOKEN ao .env; build; tools migrate e
tools migrate-mlflow antes de up. Para publicar, execute
`python deployment/scripts/publish_models.py --model CHAVE` após aprovação e depois
`docker compose -f compose.yaml -f .runtime/models.compose.json up -d --wait`.
[Fluxo completo](../operations/C3_TRAINING.md).
