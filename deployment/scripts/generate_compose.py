"""Author Compose JSON/YAML without requiring PyYAML on Windows."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
shared = dict(DB_HOST="postgres", RABBITMQ_HOST="rabbitmq", RUNTIME="compose",
    MLFLOW_TRACKING_URI="http://mlflow:5000", MLFLOW_S3_ENDPOINT_URL="http://rustfs:9000",
    S3_BUCKET="pucpr-poc", API_URI="http://api:8000", INFERENCE_URI="http://inference:8001",
    MONITOR_URI="http://monitoramento:8010", DASHBOARD_URI="http://dashboard:8088",
    INGESTION_URI="http://ingestion:8020")
services = {}


def secret(keys):
    return {key: '${' + key + ':?Configure .env}' for key in keys.split()}


def base(name, image, port=None):
    item = dict(image=image, restart="unless-stopped", logging={"driver": "json-file",
        "options": {"max-size": "10m", "max-file": "3"}},
        labels={"io.marista.environment":"poc","io.marista.solution":"horarios-inteligentes"})
    if port:
        item['ports'] = [f'127.0.0.1:{port}:{port}']
    services[name] = item
    return item


def health(item, command):
    item['healthcheck'] = dict(test=['CMD', *command], interval='30s', timeout='60s', retries=5, start_period='90s')


def deps(item, names):
    item['depends_on'] = {name: {'condition': 'service_healthy'} for name in names.split()}


p = base('postgres', 'postgres:15.10-bookworm')
p.update(environment=secret('POSTGRES_PASSWORD'), volumes=['postgres:/var/lib/postgresql/data'])
health(p, ['pg_isready', '-U', 'postgres'])
r = base('rustfs', 'rustfs/rustfs:1.0.0', 9000)
r.update(command=['/data'], volumes=['rustfs:/data'], environment={
    'RUSTFS_ACCESS_KEY': '${AWS_ACCESS_KEY_ID:?Configure .env}',
    'RUSTFS_SECRET_KEY': '${AWS_SECRET_ACCESS_KEY:?Configure .env}',
    'RUSTFS_CONSOLE_ENABLE': 'true', 'RUSTFS_ADDRESS': ':9000', 'RUSTFS_CONSOLE_ADDRESS': ':9001'})
r['ports'].append('127.0.0.1:9001:9001')
health(r, ['curl', '-fsS', 'http://127.0.0.1:9000/health'])
r = base('rabbitmq', 'rabbitmq:4.0.5-management', 15672)
r.update(environment={'RABBITMQ_DEFAULT_USER': 'poc', 'RABBITMQ_DEFAULT_PASS': '${RABBITMQ_PASSWORD:?Configure .env}'}, volumes=['rabbitmq:/var/lib/rabbitmq'])
health(r, ['rabbitmq-diagnostics', '-q', 'ping'])

definitions = [
 ('mlflow', 5000, 'MLFLOW_PASSWORD AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY', 'postgres rustfs'),
 ('ingestion', 8020, 'APP_PASSWORD AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY INGESTION_TOKEN', 'postgres rustfs mlflow'),
 ('inference', 8001, 'READONLY_PASSWORD AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY INFERENCE_TOKEN', 'postgres rustfs mlflow'),
 ('api', 8000, 'APP_PASSWORD RABBITMQ_PASSWORD API_TOKEN INFERENCE_TOKEN OPERATOR_TOKEN AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY', 'inference rabbitmq'),
 ('worker', None, 'APP_PASSWORD RABBITMQ_PASSWORD INFERENCE_TOKEN AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY', 'inference rabbitmq'),
 ('monitoramento', 8010, 'READONLY_PASSWORD MONITOR_TOKEN', 'postgres'),
 ('dashboard', 8088, 'READONLY_PASSWORD DASHBOARD_TOKEN', 'api monitoramento'),
 ('jupyter', 8888, 'AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY API_TOKEN JUPYTER_TOKEN INGESTION_TOKEN', 'api mlflow ingestion'),
]
for name, port, keys, dependencies in definitions:
    item = base(name, 'marista-jupyter:compose' if name == 'jupyter' else 'marista-app:compose', port)
    item['build'] = dict(context='.', dockerfile=f'deployment/docker/{"jupyter" if name == "jupyter" else "api"}/Dockerfile')
    item['environment'] = {**shared, **secret(keys)}
    item['mem_limit'] = '3g' if name == 'jupyter' else '2g'
    if name == 'mlflow':
        command = ['python', '-m', 'src.common.launch', 'mlflow']
        item['environment']['MLFLOW_WORKERS'] = '1'
    elif name == 'jupyter':
        command = ['/usr/local/bin/_entrypoint.sh', 'python', '-m', 'src.common.launch', 'jupyter']
        item['volumes'] = ['./workspace:/workspace']
    elif name == 'worker':
        command = ['celery', '-A', 'src.workers.tasks:app', 'worker', '--beat', '--schedule=/tmp/celerybeat-schedule', '--loglevel=INFO', '--concurrency=2']
    else:
        module = {'monitoramento':'monitoring', 'dashboard':'dashboard', 'api':'api', 'inference':'inference', 'ingestion':'ingestion'}[name]
        command = ['python', '-m', 'uvicorn', f'src.{module}.main:app', '--host', '0.0.0.0', '--port', str(port)]
    if name == 'dashboard':
        item['volumes'] = ['./data/compose-logs:/logs:ro']
    item['command'] = command
    check = ['python', '-m', 'src.common.service_check', name]
    if name == 'jupyter':
        check.insert(0, '/usr/local/bin/_entrypoint.sh')
    health(item, check)
    deps(item, dependencies)

services['tools'] = dict(image='marista-app:compose', profiles=['tools'],
    environment={**shared, **secret('POSTGRES_PASSWORD MIGRATION_PASSWORD APP_PASSWORD READONLY_PASSWORD MLFLOW_PASSWORD AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY RABBITMQ_PASSWORD API_TOKEN INFERENCE_TOKEN DASHBOARD_TOKEN INGESTION_TOKEN')},
    volumes=['./artifacts/reports:/reports'],
    entrypoint=['python', '-m', 'src.common.cli'])
services['volume-tools'] = dict(image='postgres:15.10-bookworm', profiles=['tools'], user='0:0',
    volumes=['rustfs:/restore/rustfs'], entrypoint=['sh'])
journey = dict(
    SOURCE_DATABASE_URL='postgresql+psycopg://planning_readonly:${READONLY_PASSWORD:?Configure .env}@postgres:5432/planejamento_db',
    APPLICATION_DATABASE_URL='postgresql+psycopg://planning_app:${APP_PASSWORD:?Configure .env}@postgres:5432/planejamento_db',
    MLFLOW_UI_BASE_URL='http://127.0.0.1:5000',
    MLFLOW_SUPPRESS_PRINTING_URL_TO_STDOUT='true',
    MLFLOW_PRINT_MODEL_URLS_ON_CREATION='false',
    MLFLOW_NOTEBOOK_TRACE_RENDERER_BASE_URL='http://127.0.0.1:5000',
    MLFLOW_EXPERIMENT_NAME='${MLFLOW_EXPERIMENT_NAME:-planilha-turmas-proxy-v1}', MODEL_NAME='planilha-turmas-demo',
    JOURNEY_MODE='DEMO', JOURNEY_TIMEOUT='15', JOURNEY_RETRIES='2',
    MLFLOW_HTTP_REQUEST_TIMEOUT='15', MLFLOW_HTTP_REQUEST_MAX_RETRIES='2')
for name in ('tools', 'jupyter'):
    services[name]['environment'].update(journey)
services['jupyter']['environment'].update(secret('INFERENCE_TOKEN'))
for name in ('api','worker'):
    services[name]['environment'].update({key:value for key,value in journey.items() if key not in ('SOURCE_DATABASE_URL','APPLICATION_DATABASE_URL')})
services['api']['environment']['OPERATOR_ID']='poc-reviewer'
services['jupyter']['environment'].update(secret('OPERATOR_TOKEN'))
services['tools']['environment'].update(secret('OPERATOR_TOKEN'))
services['jupyter']['environment']['PROPOSAL_ID'] = '${PROPOSAL_ID:-}'
services['jupyter']['volumes'] += ['./artifacts/reports:/reports']
for name in ('jupyter', 'api', 'inference','worker'):
    services[name]['environment']['MLFLOW_EXPERIMENT_NAME'] = journey['MLFLOW_EXPERIMENT_NAME']
    services[name]['environment']['MLFLOW_ENABLE_ASYNC_TRACE_LOGGING'] = 'false'
    services[name]['environment']['EVENT_DIRECTORY'] = '/logs'
    services[name].setdefault('volumes', []).append('./data/compose-logs:/logs')

document = dict(name='marista', services=services, volumes={key:{} for key in ['postgres','rustfs','rabbitmq']})
if '--check' in sys.argv:
    assert document == json.loads((ROOT / 'compose.yaml').read_text()), 'Compose generator drift'
    print('PASS Compose generator matches manifest')
    sys.exit(0)
(ROOT / 'compose.yaml').write_text(json.dumps(document, indent=2)+'\n', encoding='utf-8')
