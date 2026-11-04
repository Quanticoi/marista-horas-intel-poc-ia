"""Consolidate existing V3 evidence without converting automatic checks into UI acceptance."""
import json
import hashlib
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'artifacts/reports/v3'


def read(name):
    path=REPORT/name
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}


def metadata(name):
    value=read(name) if name.endswith('.json') else {}
    return value if isinstance(value,dict) else {}


def main():
    head=subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),'rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    now=datetime.now(timezone.utc).isoformat()
    scenario=read('scenario-latest.json');preservation=read('preservation-after.json')
    notebooks=read('isolated/notebook-suite.json');negative=read('isolated/negative.json')
    serving=read('isolated/serving.json');reset=read('reset-isolated-proof.json')
    ui=read('ui-observations.json');runtime=read('runtime-after.json')
    suites=ET.parse(REPORT/'main-suite-junit.xml').getroot().findall('testsuite')
    tests=sum(int(s.get('tests','0')) for s in suites)
    errors=sum(int(s.get('errors','0'))+int(s.get('failures','0')) for s in suites)
    assert tests>=85 and errors==0,'Latest principal tests did not pass'
    assert preservation.get('status')=='AUTO_PASS','Preservation proof required'
    assert notebooks.get('status')=='PASS','Complete notebook evidence required'
    assert len({r['notebook'] for r in notebooks['evidence'] if r['status']=='PASS'})==10
    assert negative.get('status')==serving.get('status')=='AUTO_PASS'
    assert reset.get('status')=='PASS' and len(reset['resets'])==2
    assert isinstance(runtime,list) and len(runtime)==11 and all(s['Health']=='healthy' for s in runtime)
    items=scenario['items'];proofs=[i['result'] for i in items]
    assert len({p['artifact_sha256'] for p in proofs})==3
    criteria=[
        ('01','AUTO_PASS','runtime-after.json','Onze serviços healthy; diagrama de startup preservado.'),
        ('02',ui.get('mlflow_status','MANUAL_NOT_CHECKED'),'ui-observations.json','SDK comprova nomes/tags/Registry; UI exige observação real registrada.'),
        ('03','AUTO_PASS','isolated/notebooks/04-train.ipynb','Treino e repetição idempotente em kernel novo, tabela Onde conferir.'),
        ('04','AUTO_PASS','isolated/notebooks/05-campaign-30.ipynb','Campanha real com 30 escopos DEMO; default manual permanece três.'),
        ('05','AUTO_PASS','scenario-latest.json','Catálogo imutável aponta para três arquivos originais; sem duplicar binário.'),
        ('06','AUTO_PASS','main-suite-junit.xml','Comparação byte a byte proxy/S3, hash Registry/catálogo e assinatura.'),
        ('07','AUTO_PASS','main-suite-junit.xml','Quatro views e consultas parametrizadas; nove ofertas com três contribuições.'),
        ('08','AUTO_PASS','scenario-latest.json','Auditoria reversa verifica run/versão/snapshot/manifests/atribuição de linhas.'),
        ('09','AUTO_PASS','isolated/notebooks/02-generate.ipynb','Geração HTTP por API/worker e conferência SQL, sem treino no notebook02.'),
        ('10','AUTO_PASS','isolated/serving.json','Jupyter parado; cache vazio após restart; três modelos recarregados.'),
        ('11','AUTO_PASS','reset-isolated-proof.json','Rebootstrap empty saudável sem modelos; saúde/registro/cache/aprovação distintos.'),
        ('12','AUTO_PASS','isolated/negative.json','Revisão explícita DEMO; revogação bloqueia APPROVED com cache quente.'),
        ('13','AUTO_PASS','preservation-after.json','Histórico preservado; versões sem catálogo completo permanecem LEGACY_PARTIAL.'),
        ('14','AUTO_PASS','scenario-latest.json','Três períodos DEMO distintos, três SHA256 e segunda versão com alpha diferente.'),
        ('15',ui.get('session_status','MANUAL_NOT_CHECKED'),'ui-observations.json','Roteiro completo e pacote JSON/Markdown/CSV; inspeção de todas as interfaces ainda necessária.'),
        ('16','AUTO_PASS','isolated/negative.json','Artefatos/tags/assinatura/manifest divergentes, snapshot errado, versão ausente, auth e revogação rejeitados.'),
        ('17','NOT_EXECUTED','../../../.github/workflows/compose.yml','CI remoto não executado e fora do fechamento local solicitado pelo usuário. Pipeline contém testes novos; nenhum commit/PR foi criado.'),
        ('18','AUTO_PASS','acceptance-v3.json','Estados automáticos, manuais e bloqueados separados; nenhum 20/20 fabricado.'),
        ('19','AUTO_PASS','reset-isolated-proof.json','Reset-data/empty e factory-reset/demo-ready somente isolados; arquivos protegidos conferidos.'),
        ('20','AUTO_PASS','preservation-after.json','83 runs, 57 versões, 395 objetos, 22 propostas e dez notebooks anteriores preservados.'),
    ]
    limitations=[
        'Base Git '+head+' com alterações locais: não é um commit que contenha a V3. Não houve commit, push ou PR.',
        'Cada prova conserva sua data e versão de código; resets ocorreram antes do reforço final da auditoria. Migração e controlador não mudaram depois do ensaio.',
        'Por orientação posterior do usuário, a entrega é do código pronto para teste local. Conferência visual fica com o usuário; CI remoto não é condição para esta entrega. Nenhum resultado não executado foi marcado PASS.',
        '500 ensaios V2 são baseline histórico de orquestração sobre o mesmo dataset/um SHA; não certificam V3 ou 500 comportamentos. V3 executou campanha de 30 escopos e prova de três modelos distintos.',
        'DEMO e contrato provisório; V4.4, PRIME, dados reais, produção/GCP e SLO não homologados.',
        'Catálogo SQL 1.1 indexa novas versões. Registro antigo sem contexto suficiente não recebe backfill inventado; consultar Registry/lineage e LEGACY_PARTIAL.',
        'O inventário anterior não continha aprovações: nenhuma aprovação histórica principal foi exercitada na prova de preservação; governança foi testada no isolado.',
    ]
    matrix=[dict(test_id='V3-'+number,status=status,evidence_file=path,checks=[note],git_commit=None,
        base_git_commit=head,code_version=metadata(path).get('code_version'),
        environment='poc',source_type='DEMO',report_generated_at_utc=now,
        executed_at_utc=metadata(path).get('executed_at_utc',metadata(path).get('timestamp_utc')),
        manual_observation=ui if number in ('02','15') else None) for number,status,path,note in criteria]
    document=dict(report_generated_at_utc=now,base_git_commit=head,tested_git_commit=None,
        code_version=preservation['code_version'],working_tree_uncommitted=True,tests=tests,failures=errors,
        status='READY_FOR_LOCAL_TEST',acceptance_status='AUTOMATED_CHECKS_PASSED_MANUAL_TEST_BY_USER',criteria=matrix,counts=dict(Counter(r['status'] for r in matrix)),
        proposal_id=scenario['proposal_id'],campaign_id=scenario['campaign_id'],models=proofs,limitations=limitations)
    (REPORT/'acceptance-v3.json').write_text(json.dumps(document,default=str,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Entrega V3 — pronta para teste local',
        '',f"Gerado em {now}. **Implementação finalizada; {tests} testes passaram, zero falhas.** Conforme orientação do usuário, a conferência local fica a seu cargo. UI e CI remoto não impedem esta entrega; a matriz mantém os resultados efetivamente executados.",
        '',f'Base Git: `{head}`. V3 ainda não commitada. Código da imagem principal verificada: `{preservation["code_version"]}`.',
        '', '[JSON completo](acceptance-v3.json) · [Roteiro manual](../../../docs/operations/MANUAL_ACCEPTANCE_V3.md) · [SQL](../../../docs/operations/SQL_VALIDATION_V3.md)',
        '', '| Critério | Estado | Evidência e alcance |','|---|---|---|']
    lines += [f'| V3-{number} | {status} | [{note}]({path}) |' for number,status,path,note in criteria]
    lines += ['', '## Sessão principal disponível para conferência', '',
        f"Proposta: `{scenario['proposal_id']}`; campanha: `{scenario['campaign_id']}`; snapshot: `{scenario['snapshot_id']}`.",
        '', '| Modelo DEMO | Versão | Run / Registry | Manifest |','|---|---|---|---|']
    for item in items:
        result=item['result'];name=item['model_key'];version=item['model_version'];eid=result['experiment_id'];run=result['run_id']
        lines.append(f"| {name} | {version} | [Run {run[:8]}](http://localhost:5000/#/experiments/{eid}/runs/{run}) · [Registry](http://localhost:5000/#/models/{name}/versions/{version}) | `{result['catalog']['manifest_uri']}` |")
    lines+=['','## Alterações e persistência','',
        '- HI-LINEAGE/1.1: nomes por códigos sintéticos reais, experimento por ciclo, tags coerentes e versão explícita.',
        '- planning.model_version_catalog + quatro views; dados de negócio permanecem em planejamento_db. mlflow_db continua exclusivamente administrado pelo MLflow.',
        '- RustFS mantém binários originais em mlflow/ e catálogo legível em lineage/. Manifests são condicionais e imutáveis.',
        '- Auditoria autenticada, filtros no dashboard, dez notebooks e exportação de sessão com links diretos e CSV de objetos.',
        '- Assinatura/hash validados antes da desserialização; tags conferidas mesmo com cache quente; limite de quatro versões por processo.',
        '', '## Executar e reproduzir','',
        '```powershell','.\deployment\scripts\compose.ps1 start',
        '# Para aplicar alterações futuras, preservando dados:', '.\deployment\scripts\compose.ps1 rebuild',
        '# Conferir testes:', '.\deployment\scripts\compose.ps1 test',
        'python tests/acceptance/jupyter_editability.py --report-version v3',
        'python tests/acceptance/report_v3.py','```','',
        'Abra [Jupyter](http://localhost:8888), execute 00; use 04/05 para treino, 02 para geração e 08 para auditoria. 01 continua demonstração legada. Configuração de escrita explícita no roteiro manual.',
        '', '[MLflow](http://localhost:5000) · [RustFS](http://localhost:9001) · [API](http://localhost:8000/docs) · [Dashboard](http://localhost:8088)',
        '', '## Limitações e pendências','']+[f'- {item}' for item in limitations]
    (REPORT/'acceptance-v3.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    index=[dict(path=p.relative_to(REPORT).as_posix(),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
           for p in sorted(REPORT.rglob('*')) if p.is_file() and p.name!='evidence-index.json']
    (REPORT/'evidence-index.json').write_text(json.dumps(dict(generated_at_utc=now,files=index),indent=2),encoding='utf-8')
    print(json.dumps(document['counts']))


if __name__=='__main__':
    main()
