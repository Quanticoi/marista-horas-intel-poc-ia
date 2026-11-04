"""Execute one catalog notebook in a fresh container kernel; preserve user copies."""
import argparse
import os
from pathlib import Path
import nbformat
from nbclient import NotebookClient


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("notebook")
    parser.add_argument("--proposal-id")
    parser.add_argument("--reset-plan-id")
    parser.add_argument("--workspace",action="store_true",help="Execute the editable notebook used in Jupyter")
    args=parser.parse_args()
    if Path(args.notebook).name!=args.notebook:
        raise ValueError("Select a source notebook by filename")
    if args.proposal_id:
        from uuid import UUID
        os.environ["PROPOSAL_ID"]=str(UUID(args.proposal_id))
    if args.reset_plan_id:
        from uuid import UUID
        os.environ["RESET_PLAN_ID"]=str(UUID(args.reset_plan_id))
    source=Path("/workspace/notebooks" if args.workspace else "/app/notebooks")/args.notebook
    notebook=nbformat.read(source,as_version=4)
    output=Path("/reports")/(source.stem+".executed.ipynb")
    try:
        NotebookClient(notebook,timeout=240,kernel_name="pucpr",resources={"metadata":{"path":"/workspace"}}).execute()
    finally:
        nbformat.write(notebook,output)
    print("PASS",source.name)


if __name__=="__main__":
    main()
