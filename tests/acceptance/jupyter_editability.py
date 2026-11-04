"""Verify saving through Jupyter after rebuild; remove only our temporary notebook."""
import argparse,json
import subprocess
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
from uuid import uuid4

root=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--report-version',choices=['v2','v3'],default='v2');args=parser.parse_args()
values=dict(line.split('=',1) for line in (root/'.env').read_text().splitlines() if '=' in line and not line.startswith('#'))
def request(method,path,body=None):
    data=json.dumps(body).encode() if body is not None else None
    req=Request('http://127.0.0.1:8888/api/contents/'+path,data=data,method=method,
                headers={'Authorization':'token '+values['JUPYTER_TOKEN'],'Content-Type':'application/json'})
    with urlopen(req,timeout=20) as response:
        raw=response.read()
        return json.loads(raw) if raw else None

listing=request('GET','notebooks')
names=sorted(p['name'] for p in listing['content'] if p['name'].endswith('.ipynb'))
expected=sorted(p.name for p in (root/'notebooks').glob('*.ipynb'))
assert names==expected and listing['writable'] and len(names)==10
assert all(p['writable'] for p in listing['content'] if p['name'] in names)
temporary='notebooks/editability-check-'+uuid4().hex+'.ipynb'
created=False
try:
    content={'nbformat':4,'nbformat_minor':5,'metadata':{},'cells':[{'cell_type':'markdown','id':'proof','metadata':{},'source':'save test'}]}
    request('PUT',temporary,{'type':'notebook','format':'json','content':content});created=True
    content['cells'][0]['source']='edited and saved'
    request('PUT',temporary,{'type':'notebook','format':'json','content':content})
    assert request('GET',temporary)['content']['cells'][0]['source']=='edited and saved'
finally:
    if created:request('DELETE',temporary)
document=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
    git_commit=subprocess.check_output(['git','-c','safe.directory='+root.as_posix(),'rev-parse','HEAD'],text=True).strip(),
    environment='poc',project='marista',test_id='jupyter-editability',source_type='DEMO',status='PASS',
    notebooks=names,save_and_reload=True,temporary_notebook_removed=True)
(root/'artifacts/reports'/args.report_version/'jupyter-editability.json').write_text(json.dumps(document,indent=2),encoding='utf-8')
print('PASS: ten writable notebooks, one main journey, save/reload verified after rebuild')
