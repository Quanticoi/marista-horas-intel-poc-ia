.PHONY: check build install verify test e2e status
COMPOSE = docker compose -f compose.yaml $(if $(wildcard .runtime/models.compose.json),-f .runtime/models.compose.json)
check:
	$(COMPOSE) config --quiet
build:
	$(COMPOSE) build mlflow jupyter
install:
	@echo "Windows: deployment/scripts/compose.ps1 init. Linux: docs/installation/LINUX.md."
verify:
	$(COMPOSE) up -d --wait --wait-timeout 300
	$(COMPOSE) run --rm --no-deps tools validate
test:
	$(COMPOSE) run --rm --no-deps --entrypoint python tools -m pytest tests/unit tests/integration -q -o cache_dir=/tmp/pytest-cache
e2e:
	$(COMPOSE) run --rm --no-deps tools e2e
status:
	$(COMPOSE) ps
