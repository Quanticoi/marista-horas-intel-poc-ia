"""Host-safe validation of source files only; does not import/run the application."""
import ast
import json
import re
import tomllib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'tests').rglob('*.py'))+list((ROOT/'dev').glob('*.py'))+list((ROOT/'deployment/scripts').glob('*.py'))
    for path in files:
        tree=ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node,ast.ImportFrom) and node.module and node.module.startswith('src.'):
                target=ROOT.joinpath(*node.module.split('.'))
                assert target.with_suffix('.py').is_file() or (target/'__init__.py').is_file(), (path,node.module)
    print(f'PASS Python AST/internal imports ({len(files)} files; no application execution)')
    project=tomllib.loads((ROOT/'pyproject.toml').read_text())
    assert all('==' in dependency for dependency in project['project']['dependencies'])
    print('PASS TOML/direct dependency pins (resolver not executed)')
    compose=json.loads((ROOT/'compose.yaml').read_text(encoding='utf-8'))
    services=compose['services']
    expected={'postgres','rustfs','rabbitmq','mlflow','inference','api','worker','monitoramento','dashboard','jupyter','ingestion'}
    assert {name for name,s in services.items() if not s.get('profiles')}==expected
    env_keys=set(re.findall(r'^([A-Z_]+)=',(ROOT/'.env.example').read_text(),re.M))
    assert set(re.findall(r'\$\{([A-Z_]+):',json.dumps(compose))) <= env_keys
    for name in expected:
        service=services[name]
        assert service['healthcheck']['test']
        assert service['logging']['options']['max-size']=='10m'
        assert all(port.startswith('127.0.0.1:') for port in service.get('ports',[]))
        for dep,condition in service.get('depends_on',{}).items():
            assert dep in expected and condition['condition']=='service_healthy'
        assert 'docker.sock' not in json.dumps(service)
    def visit(name, ancestors):
        assert name not in ancestors, ('dependency cycle',name)
        for dep in services[name].get('depends_on',{}):
            visit(dep,ancestors|{name})
    for name in expected:
        visit(name,set())
    assert './workspace:/workspace' in services['jupyter']['volumes']
    assert 'DASHBOARD_TOKEN' in services['tools']['environment']
    assert 'svc.cluster.local' not in json.dumps(compose)
    for item in services.values():
        if 'build' in item:
            assert (ROOT/item['build']['dockerfile']).is_file()
    print('PASS Compose services, dependency graph, healthchecks, loopback, secrets references and mounts')
    original=(ROOT/'dev/spec.md').read_text(encoding='utf-8')
    canonical=re.search(r'```sql\n(-- Database planejamento_db.*?)```',original,re.S).group(1)
    assert (ROOT/'sql/ddl/001_planning.sql').read_text(encoding='utf-8')==canonical
    assert len(re.findall('CREATE TABLE IF NOT EXISTS',canonical))==16
    contract=(ROOT/'spec.md').read_text(encoding='utf-8')
    assert (ROOT/'sql/ddl/002_immutability.sql').read_text(encoding='utf-8').strip() in contract
    print('PASS original DDL preserved (16 tables); additive triggers reconciled with spec')
    notebooks=list((ROOT/'notebooks').glob('*.ipynb'))
    assert len(notebooks)==11
    for path in notebooks:
        notebook=json.loads(path.read_text(encoding='utf-8'))
        for cell in notebook['cells']:
            if cell['cell_type']=='code':
                ast.parse(''.join(cell['source']),filename=str(path))
                assert cell['outputs']==[]
    print('PASS 11 notebooks JSON/code syntax; no fabricated execution outputs')
    namespaces={'training','mlops','ai-service','data','operations'}
    resources=[]
    charts=list((ROOT/'deployment/helm').glob('*/values.yaml'))
    assert len(charts)==5
    for path in charts:
        values=json.loads(path.read_text())
        assert values['storageClass']=='local-path'
        for entry in values['resources']:
            resource=entry['resource']
            resources.append(resource)
            assert resource['metadata']['namespace'] in namespaces
            assert 'hostPath' not in json.dumps(resource)
            if resource['kind']=='PersistentVolumeClaim':
                assert resource['spec']['accessModes']==['ReadWriteOnce']
                assert resource['metadata']['annotations']['helm.sh/resource-policy']=='keep'
            if resource['kind'] in ('Deployment','StatefulSet'):
                for container in resource['spec']['template']['spec']['containers']:
                    assert container['resources']['requests'] and container['resources']['limits']
                    assert ':latest' not in container['image']
            if resource['kind']=='CronJob':
                assert resource['spec']['suspend'] is True
    dashboard=next(r for r in resources if r['kind']=='Deployment' and r['metadata']['name']=='dashboard')
    assert len(dashboard['spec']['template']['spec']['containers'])==2
    assert dashboard['spec']['strategy']['type']=='Recreate'
    deployed={(r['metadata']['namespace'],r['metadata']['name']) for r in resources if r['kind']=='Deployment'}
    assert {('mlops','mlflow'),('mlops','monitoramento'),('ai-service','inference'),('ai-service','api'),('ai-service','worker')} <= deployed
    inference=next(r for r in resources if r['kind']=='Deployment' and r['metadata']['name']=='inference')
    assert inference['spec']['template']['spec']['containers'][0]['envFrom'][1]['secretRef']['name']=='poc-inference'
    roles=json.loads((ROOT/'deployment/kubernetes/rbac/collector.json').read_text())['items']
    assert all(r['kind'] not in ('ClusterRole','ClusterRoleBinding') for r in roles)
    for role in roles:
        for rule in role.get('rules',[]):
            assert set(rule['verbs'])<={'get','list','watch'}
            assert not set(rule['resources'])&{'secrets','pods/exec','*'}
    print(f'PASS Helm input JSON ({len(charts)} charts/{len(resources)} resources), RWO/RBAC/namespace guards; Helm rendering not executed')
    for path in (ROOT/'deployment/kubernetes').rglob('*.json'):
        json.loads(path.read_text())
    missing=[]
    for path in [ROOT/'README.md',*(ROOT/'docs').rglob('*.md')]:
        for link in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if not link.startswith(('http:','https:','#')) and not (path.parent/link.split('#')[0]).exists():
                missing.append((str(path.relative_to(ROOT)),link))
    assert not missing,missing
    print('PASS repository documentation links')


if __name__=='__main__':
    main()
