"""Run every V4 notebook in a fresh kernel; operational writes require explicit CLI opt-in."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime,timezone
from src.workbench.application_client import context


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--approve-demo',action='store_true')
    parser.add_argument('--workspace',action='store_true')
    args=parser.parse_args()
    env=dict(os.environ,NOTEBOOK_REPORT_DIR='/reports/v4/notebooks')
    if args.approve_demo:
        env.update(V4_APPROVE_DEMO='true',V4_DEPLOY_DEMO='true',V4_GENERATE='true')
    root=Path('/workspace/notebooks' if args.workspace else '/app/notebooks')
    notebooks=sorted(root.glob('*.ipynb'))
    if [p.name[:2] for p in notebooks]!=[f'{i:02}' for i in range(12)]:
        raise ValueError('Expected exactly twelve V4 notebooks00–11')
    results=[]
    for notebook in notebooks:
        command=['python','-m','src.workbench.execute_notebook',notebook.name]
        if args.workspace:
            command.append('--workspace')
        process=subprocess.run(command,env=env,capture_output=True,text=True,timeout=900)
        item=dict(notebook=notebook.name,status='PASS' if process.returncode==0 else 'FAIL',exit_code=process.returncode)
        results.append(item);print(json.dumps(item),flush=True)
        report=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),results=results,context=context(),
            operational_writes=args.approve_demo,manual='MANUAL_NOT_CHECKED')
        Path('/reports/v4/application-notebook-proof.json').write_text(json.dumps(report,indent=2))
        if process.returncode:
            # The executed notebook contains diagnosis. Never echo arbitrary secret-bearing output.
            raise RuntimeError('Notebook failed: '+notebook.name+'; inspect /reports/v4/notebooks executed copy')
    print('PASS: twelve fresh kernels; manual visual inspection not asserted')


if __name__=='__main__':
    main()
