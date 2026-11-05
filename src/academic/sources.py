"""Read-only source discovery. Never executes macros or invents missing inputs."""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

REQUIRED = (
    "Planilha de Turmas 2024.2_Engenharia de Computação.xlsm",
    "Planilha de Turmas 2024.2_CiberSegurança.xlsm",
    "DADOS-EXTERNOS-OTIMIZACAO-HORARIOS-V3.xlsx",
    "REQ_InteligenciaeOtimizacaodeHorariosAcademicos_V4.4 (1).pdf",
    "PUCPR - Otimização de Horários Inteligentes - Arquitetura de Componentes-V3(2).pdf",
    "PUCPR - Otimização de Horários Inteligentes - Arquitetura de Containers-V3(1).pdf",
    "PUCPR - Otimização de Horários Inteligentes - Diagrama de Sequencia-V3(1).pdf",
    "diagnostico_dados_simulacao_realista_horas_inteligentes.md",
)


def inventory(roots):
    def normalized(name):
        return re.sub(r'\s+', ' ', re.sub(r'\(\d+\)(?=\.pdf$)', '', name).replace(' .pdf','.pdf')).strip().casefold()
    rows = []
    for name in REQUIRED:
        matches = sorted({p.resolve() for root in roots if root.is_dir()
                          for p in root.rglob('*') if p.is_file() and normalized(p.name) == normalized(name)})
        hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in matches}
        status = "SOURCE_MISSING" if not matches else "AMBIGUOUS" if len(set(hashes.values())) > 1 else "FOUND"
        rows.append(dict(name=name, status=status, matches=[
            dict(path=str(p), sha256=hashes[p], bytes=p.stat().st_size) for p in matches]))
    return dict(schema_version="v4-source-inventory/1", timestamp_utc=datetime.now(timezone.utc).isoformat(),
                status="READY_FOR_INSPECTION" if all(r["status"] == "FOUND" for r in rows) else "SOURCE_MISSING_OR_AMBIGUOUS",
                searched_roots=[str(p.resolve()) for p in roots], sources=rows,
                limitations=["FOUND validates presence and hash only, not academic content or import.",
                             "No macros executed. No simulated enrollment created."])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", action="append", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/reports/v4/source_inventory.json"))
    args = parser.parse_args()
    result = inventory(args.root or [Path("reference"), Path("data/reference"), Path("dev")])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    for row in result["sources"]:
        print(row["status"] + ": " + row["name"])
    raise SystemExit(0 if result["status"] == "READY_FOR_INSPECTION" else 2)


if __name__ == "__main__":
    main()
