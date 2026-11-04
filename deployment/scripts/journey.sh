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
  rebuild) rebuild; dc exec -T jupyter /usr/local/bin/_entrypoint.sh python -m src.workbench.execute_journey; verify ;;
  journey) dc exec -T jupyter /usr/local/bin/_entrypoint.sh python -m src.workbench.execute_journey; verify ;;
  acceptance) dc exec -T jupyter /usr/local/bin/_entrypoint.sh python -m src.workbench.execute_journey; verify; dc restart mlflow; dc up -d --wait --wait-timeout 240 mlflow; verify; rebuild; verify ;;
  *) echo 'Usage: journey.sh rebuild|journey|acceptance' >&2; exit 2 ;;
esac
