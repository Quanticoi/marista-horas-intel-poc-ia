#!/usr/bin/env sh
# Docker-only equivalent. Run from repository root with the existing .env.
set -eu
python deployment/scripts/init_env.py
action="${1:-rebuild}"
dc() {
  if [ -f .runtime/models.compose.json ]; then
    docker compose -f compose.yaml -f .runtime/models.compose.json "$@"
  else
    docker compose -f compose.yaml "$@"
  fi
}
rebuild() {
  dc build mlflow jupyter
  mkdir -p workspace/notebooks data/compose-logs artifacts/reports/v2 artifacts/reports/v3
  chmod a+rwx workspace workspace/notebooks data/compose-logs
  chmod -R a+rwX artifacts/reports
  dc run --rm --no-deps --entrypoint chown volume-tools 10001:10001 /restore/rustfs
  dc up -d --wait --wait-timeout 240 postgres rustfs rabbitmq
  for step in bootstrap migrate buckets seed; do dc run --rm --no-deps tools "$step"; done
  dc up -d --wait --wait-timeout 300
}
verify() {
  dc run --rm --no-deps --entrypoint python tools -m pytest tests/integration/test_journey.py -q -o cache_dir=/tmp/pytest-cache --junitxml=/reports/journey-junit.xml
}
case "$action" in
  rebuild) rebuild ;;
  journey)
    for book in 00_ambiente 01_fontes_academicas 02_qualidade_dados 03_exploracao_demanda 04_treinamento_modelos 05_campanhas_lotes 06_avaliacao_modelos; do
      dc exec -T jupyter /usr/local/bin/_entrypoint.sh python -m src.workbench.execute_notebook "$book.ipynb"
    done
    echo 'Abra07 para revisão explícita,08 para deploy/geração e09/10 para consulta/auditoria.' ;;
  acceptance) dc run --rm --no-deps --entrypoint python tools -m pytest tests/unit tests/integration -q -o cache_dir=/tmp/pytest --junitxml=/reports/v4/acceptance-junit.xml ;;
  *) echo 'Usage: journey.sh rebuild|journey|acceptance' >&2; exit 2 ;;
esac
