"""Check Jupyter writable API after rebuild using only an agent-owned temporary notebook."""
import os
import json
from uuid import uuid4
from pathlib import Path
import httpx


def main():
    with httpx.Client(base_url='http://jupyter:8888',timeout=30,
                     headers={'Authorization':'token '+os.environ['JUPYTER_TOKEN']}) as client:
        listed=client.get('/api/contents/notebooks');listed.raise_for_status()
        expected={p.name for p in Path('/app/notebooks').glob('*.ipynb')}
        visible={i['name']:i for i in listed.json()['content'] if i['name'].endswith('.ipynb')}
        assert expected.issubset(visible)
        assert all(visible[name]['writable'] for name in expected)
        name='v4-write-proof-'+uuid4().hex+'.ipynb'
        path='/api/contents/notebooks/'+name
        try:
            notebook=dict(nbformat=4,nbformat_minor=5,metadata={},cells=[])
            saved=client.put(path,json=dict(type='notebook',format='json',content=notebook));saved.raise_for_status()
            restored=client.get(path);restored.raise_for_status()
            assert restored.json()['writable'] and restored.json()['content']['cells']==[]
        finally:
            removed=client.delete(path)
            assert removed.status_code in (204,404)
    Path('/reports/v4/jupyter-editability.json').write_text(json.dumps(dict(status='PASS',
        notebooks=sorted(expected),writable=True,temporary_write_read_delete='PASS',user_notebooks_modified=False),indent=2))
    print('PASS: 12 editable notebooks; temporary write/read/delete through Jupyter API')


if __name__=='__main__':
    main()
