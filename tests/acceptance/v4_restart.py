"""Called by an external controller after stopping Jupyter/restarting inference."""
import json
import os
from pathlib import Path
from uuid import uuid4
import httpx
from src.workbench.academic_data import load,prepare,FEATURES


def main():
    evidence=json.loads(Path('/reports/v4/training-cohort-evidence.json').read_text())
    client=httpx.Client(base_url=os.environ['INFERENCE_URI'],timeout=120,
        headers={'Authorization':'Bearer '+os.environ['INFERENCE_TOKEN']})
    before=client.get('/internal/academic/runtime');before.raise_for_status()
    assert len(before.json()['versions'])==1, 'Only explicitly PRELOAD model should be resident after restart'
    assert before.json()['versions'][0]['model_name']==evidence['models'][0]['model_name']
    frame,_=load(evidence['snapshot_id'])
    results=[]
    for model in evidence['models']:
        _,_,future=prepare(frame,model['course_code'])
        body=dict(model_name=model['model_name'],model_version=model['model_version'],snapshot_id=evidence['snapshot_id'],
            records=future[FEATURES].head(2).to_dict('records'),correlation_id=str(uuid4()))
        response=client.post('/internal/academic/predict',json=body);response.raise_for_status()
        result=response.json()
        assert result['run_id']==model['run_id'] and result['artifact_sha256']==model['artifact_sha256']
        results.append(result)
    after=client.get('/internal/academic/runtime');after.raise_for_status()
    assert len(after.json()['versions'])==3
    Path('/reports/v4/restart-inference.json').write_text(json.dumps(dict(status='PASS',before=before.json(),after=after.json(),predictions=results),indent=2))
    print('PASS: 1 PRELOAD and 2 LAZY models recovered with persisted checksums')


if __name__=='__main__':
    main()
