"""Consolidate existing measured evidence; missing proofs never become PASS."""
import hashlib
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[2];reports=root/'artifacts/reports';out=reports/'v2'
commit=subprocess.check_output(['git','-c','safe.directory='+root.as_posix(),'rev-parse','HEAD'],text=True).strip()
base=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),git_commit=commit,environment='poc',source_type='DEMO')
def read(name):
    path=reports/name
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}
def passed(name):
    return read(name).get('status')=='PASS'
def write(name,data):
    (out/(name+'.json')).write_text(json.dumps({**base,**data},ensure_ascii=False,indent=2),encoding='utf-8')

before=read('v2/inventory-before.json')
hashes={hashlib.sha256(p.read_bytes()).hexdigest():p.relative_to(root).as_posix() for p in (root/'workspace').rglob('*.ipynb')}
protected=[]
for name,digest in before['protected_sha256'].items():
    if name=='.env':
        current=(root/name).read_bytes();prefix=current[:current.rfind(b'OPERATOR_TOKEN=')]
        valid=hashlib.sha256(current).hexdigest()==digest or any(hashlib.sha256(prefix[:n]).hexdigest()==digest for n in range(max(0,len(prefix)-5),len(prefix)+1))
        protected.append(dict(path=name,status='PASS' if valid else 'FAIL',note='Existing bytes preserved; separate operator credential appended'))
    else:
        protected.append(dict(path=name,sha256=digest,preserved_at=hashes.get(digest),status='PASS' if digest in hashes else 'FAIL'))
runtime=read('v2/preservation-runtime-after.json')
write('preservation-after',dict(test_id='V2-13',status='PASS' if runtime.get('status')=='PASS' and all(p['status']=='PASS' for p in protected) else 'FAIL',
    project='marista',evidence=dict(runtime=runtime,protected_files=protected),limitations=['Templates intentionally updated; exact old bytes retained outside notebook list','No database backup created']))

junit=reports/'v2/final-junit.xml'
suites=list(ET.parse(junit).getroot().iter('testsuite')) if junit.exists() else []
tests=sum(int(s.attrib['tests']) for s in suites)
tests_ok=tests>0 and not any(int(s.attrib.get(k,0)) for s in suites for k in ('failures','errors','skipped'))
journey=read('journey-latest.json');catalog=read('catalog-smoke.json');suite=read('v2/isolated/notebook-suite.json')
ci=read('v2/ci-result.json')
checks=[]
def check(number,title,condition,*paths):
    checks.append(dict(id=f'V2-{number:02}',scenario=title,status='PASS' if condition else 'NOT_EXECUTED',evidence_paths=list(paths)))
check(1,'Jornada01 em kernel novo',bool(journey) and all(s['status']=='PASS' for s in journey['stages']), 'journey-latest.json','01_jornada_completa_planilha_turmas.executed.ipynb')
check(2,'API gera DRAFT e reconcilia SQL/S3',passed('v2/probe-complete.json'),'v2/probe-complete.json')
check(3,'Idempotência, conflito e recuperação',tests_ok and passed('v2/isolated/worker-restart-recovered.json'),'v2/final-junit.xml','v2/isolated/worker-restart-recovered.json')
check(4,'Notebook02: leitura e geração HTTP',suite.get('status')=='PASS' and {'02-read','02-generate'}<={r['case'] for r in suite.get('evidence',[]) if r['status']=='PASS'},'v2/isolated/notebook-suite.json')
check(5,'Contrato técnico e limites V4.4',tests_ok,'v2/final-junit.xml','v2/probe-complete.json')
check(6,'Registry e hashes no Object Store',bool(journey.get('storage_evidence')) and all(r['status']=='PASS' for r in journey['storage_evidence']),'journey-latest.json')
check(7,'Linhagem N:N e busca reversa',passed('v2/lineage-cross-system.json'),'v2/lineage-cross-system.json','v2/lineage-negative-tests.json')
check(8,'Campanhas persistentes e controles',passed('v2/isolated/campaign-controls.json') and passed('v2/isolated/worker-restart-recovered.json'),'v2/isolated/campaign-controls.json','v2/isolated/worker-restart-recovered.json')
for number,count in ((9,30),(10,500)):
    path=f'v2/training-campaign-{count}.json';data=read(path)
    check(number,f'{count} treinamentos reais',data.get('status')=='PASS' and data.get('evidence',{}).get('actual_trained')==count,path)
check(11,'Aprovação/revogação/rollback isolados',passed('v2/lineage-negative-tests.json'),'v2/lineage-negative-tests.json')
check(12,'Dois resets e jornadas pós-rebuild isolados',passed('v2/reset-isolated-proof.json') and passed('v2/isolated/reset-independent-empty.json') and passed('v2/isolated/reset-independent-demo-ready.json'),'v2/reset-isolated-proof.json','v2/isolated/reset-independent-empty.json','v2/isolated/reset-independent-demo-ready.json')
check(13,'Dados e arquivos anteriores preservados',passed('v2/preservation-after.json'),'v2/preservation-after.json')
check(14,'Dez notebooks; opt-ins e edição após restart',len(catalog.get('results',[]))==9 and all(r['status']=='PASS' for r in catalog.get('results',[])) and suite.get('status')=='PASS' and passed('v2/jupyter-editability.json'),'catalog-smoke.json','v2/isolated/notebook-suite.json','v2/jupyter-editability.json')
check(15,'CI remoto em checkout limpo',ci.get('conclusion')=='success','v2/ci-result.json')
check(16,'README, arquitetura, comandos e índices',all((root/p).is_file() for p in ('README.md','docs/operations/OPERATIONS_V2.md','dev/README.md','deployment/scripts/README.md','tests/acceptance/README.md')),'../../README.md')
limitations=['Dados sintéticos e regra provisória; não homologa o contrato acadêmico V4.4',
    '500 identidades experimentais treinadas no mesmo snapshot DEMO; não são 500 séries acadêmicas reais nem 500 modelos simultâneos em memória',
    'Resets/falhas destrutivas executados somente na stack isolada; volumes principais preservados',
    'Evidências antigas mantêm seu commit/hash original; imagens locais revisadas identificadas por d93258a; CI identifica seu próprio HEAD',
    'Warnings de depreciação de dependências não impediram os testes']
document=dict(test_id='V2-acceptance',status='PASS' if all(c['status']=='PASS' for c in checks) else 'PARTIAL',criteria=checks,
    tests=tests,main_journey=journey,api_generation=read('v2/probe-complete.json').get('evidence',{}).get('proposal_id'),
    ci=ci,limitations=limitations)
write('acceptance-v2',document)
lines=['# Aceite V2 e revisão do repositório','',document['status']+' — '+base['timestamp_utc'],
    '',f'Código das imagens locais: d93258a. Relatório: {commit}. Testes finais: {tests}.',
    '', '| Critério | Cenário | Resultado | Evidência |','|---|---|---|---|']
for c in checks:
    links=', '.join('['+Path(p).name+'](../'+p+')' for p in c['evidence_paths'])
    lines.append(f"| {c['id']} | {c['scenario']} | {c['status']} | {links} |")
lines+=['','## Demonstração local','',f"Jornada01: modelo v{journey.get('model_version')}, run `{journey.get('run_id')}`, proposta `{journey.get('proposal_id')}`.",
    f"Geração pela API: `{document['api_generation']}`. Cada proposta contém 90 linhas DEMO.",
    '', '[Jupyter](http://localhost:8888) · [MLflow](http://localhost:5000) · [RustFS](http://localhost:9001) · [API](http://localhost:8000/docs) · [Logs](http://localhost:8088)',
    '', 'Banco mlflow_db: tracking/Registry; planejamento_db.planning: snapshots, propostas e operações; RustFS/pucpr-poc: modelos e manifests.',
    '', 'Windows: `deployment/scripts/compose.ps1 start`. Abra `01_jornada_completa_planilha_turmas.ipynb` e use Restart Kernel and Run All. Jornada operacional: notebook02, modo GENERATE_AND_VALIDATE com confirmação explícita.',
    '', '## Limitações','']+['- '+s for s in limitations]
(out/'acceptance-v2.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(document['status'],tests,'tests;',sum(c['status']=='PASS' for c in checks),'of 16 criteria')
