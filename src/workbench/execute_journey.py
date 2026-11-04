"""Execute the principal notebook in a fresh kernel inside Jupyter's container."""
import json
import argparse
from pathlib import Path
import nbformat
from nbclient import NotebookClient


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--workspace",action="store_true")
    args=parser.parse_args()
    source = Path("/workspace/notebooks" if args.workspace else "/app/notebooks")/"01_jornada_completa_planilha_turmas.ipynb"
    output = Path("/reports/01_jornada_completa_planilha_turmas.executed.ipynb")
    notebook = nbformat.read(source, as_version=4)
    nbformat.validate(notebook)
    client = NotebookClient(notebook, timeout=240, kernel_name="pucpr",
        resources={"metadata":{"path":"/workspace"}}, allow_errors=False)
    try:
        client.execute()
    finally:
        output.parent.mkdir(parents=True, exist_ok=True)
        nbformat.write(notebook, output)
    reports = sorted(Path("/workspace/reports").glob("journey-*.json"), key=lambda p:p.stat().st_mtime)
    if not reports:
        raise RuntimeError("Notebook produced no execution evidence")
    summary = json.loads(reports[-1].read_text())
    # This pointer identifies an execution report, never selects a model version.
    Path("/reports/journey-latest.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
