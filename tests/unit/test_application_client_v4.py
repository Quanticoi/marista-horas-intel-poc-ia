import copy
import json
from pathlib import Path
import pytest
from src.workbench import application_client as client
from src.common.lineage import sha256


def fixture_page():
    source=Path('artifacts/reports/v4/application-view-example.json')
    return json.loads(source.read_text(encoding='utf-8'))


def test_http_client_rejects_duplicate_pagination(monkeypatch):
    original=fixture_page()
    first=copy.deepcopy(original)
    first.update(offers=original['offers'][:1],limit=1,offset=0,total_rows=2)
    second=copy.deepcopy(first);second['offset']=1
    for page in (first,second):
        page['payload_sha256']=sha256({k:v for k,v in page.items() if k!='payload_sha256'})
    pages=iter((first,second))
    monkeypatch.setattr(client,'call',lambda *a,**k:next(pages))
    with pytest.raises(ValueError,match='duplicada'):
        client.fetch(original['proposal_id'],page_size=1)


def test_http_client_rejects_tampered_hash(monkeypatch):
    page=fixture_page();page['offers'][0]['academic']['course_code']='9999'
    monkeypatch.setattr(client,'call',lambda *a,**k:page)
    with pytest.raises(ValueError,match='hash'):
        client.fetch(page['proposal_id'],page_size=page['limit'])


def test_distribution_archives_only_prior_templates(tmp_path):
    from src.common.notebook_distribution import distribute
    source=tmp_path/'source';source.mkdir()
    workspace=tmp_path/'workspace'/'notebooks';workspace.mkdir(parents=True)
    (source/'00_new.ipynb').write_text('new')
    (workspace/'00_old.ipynb').write_text('user edits')
    (workspace/'personal.ipynb').write_text('personal')
    (workspace/'.distribution.json').write_text(json.dumps({'00_old.ipynb':'old-sha'}))
    distribute(source,workspace)
    assert not (workspace/'00_old.ipynb').exists()
    assert (workspace/'personal.ipynb').read_text()=='personal'
    assert next((workspace.parent/'notebook-backups').glob('00_old.*.ipynb')).read_text()=='user edits'
    (workspace/'00_new.ipynb').write_text('new edits')
    distribute(source,workspace)
    assert (workspace/'00_new.ipynb').read_text()=='new edits'
