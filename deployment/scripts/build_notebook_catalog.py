"""Generate auditable, parameterized notebooks; no execution or deployment."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def notebook(name,title,sections):
    cells=[dict(cell_type="markdown",metadata={},source=f"# {title}\n\nPOC DEMO — contrato PROVISÓRIO / PENDENTE DE HOMOLOGAÇÃO. Execute em kernel novo. Credenciais somente por ambiente.\n")]
    for objective,code in sections:
        cells.extend([dict(cell_type="markdown",metadata={},source=objective),
                      dict(cell_type="code",metadata={},source=code,outputs=[],execution_count=None)])
    for i,c in enumerate(cells):
        c["id"]=f"catalog-{i}"
    body=dict(nbformat=4,nbformat_minor=5,cells=cells,metadata={"kernelspec":{"name":"pucpr","display_name":"PUCPR Python 3.12","language":"python"}})
    (ROOT/"notebooks"/f"{name}.ipynb").write_text(json.dumps(body,ensure_ascii=False,indent=1),encoding="utf-8")


setup='''import os, json
import pandas as pd
from IPython.display import display, Markdown
from src.workbench.journey_config import Settings
cfg=Settings.load()
'''
from catalog_v2 import build
build(notebook,setup)
print("Generated V2 catalog; no execution")
