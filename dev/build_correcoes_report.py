"""Consolidate observed acceptance evidence; never infer an unexecuted test as PASS."""
import json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPORTS=ROOT/"artifacts/reports"


def read(name):
    return json.loads((REPORTS/name).read_text(encoding="utf-8-sig"))


journey=read("journey-latest.json")
base=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),branch="development",
          tested_commit="feebce942e982bde2723ae82f1ef220f2c269438",environment="poc",
          execution_id=journey["execution_id"],run_id=journey["run_id"],model_name=journey["model_name"],
          model_version=journey["model_version"],snapshot_id=journey["snapshot_id"],proposal_id=journey["proposal_id"])
tests=[]
evidence={
 "AC-01":("01_jornada_completa_planilha_turmas.executed.ipynb","Kernel novo, jornada integral"),
 "AC-02":("journey-latest.json","1050 linhas SQL, hashes distintos de snapshot/extração"),
 "AC-03":("journey-latest.json","fit/predict reais, MAE/RMSE, Registry"),
 "AC-04":("journey-latest.json","Três arquivos comparados byte a byte via SHA256"),
 "AC-05":("compose-junit.xml","Idempotência, conflito e rollback testados"),
 "AC-06":("journey-latest.json","90 linhas reconciliadas SQL/API"),
 "AC-07":("compose-junit.xml","Lookup reverso por proposta/run/modelo/snapshot"),
 "AC-08":("02_teste_inferencia_planilha_turmas.executed.ipynb","HTTP real, páginas e schema"),
 "AC-09":(f"inference-contract-{journey['execution_id']}.json","Regras não demonstradas marcadas NOT_EVALUATED"),
 "AC-10":("compose-junit.xml","Rotas antigas preservadas e contrato aditivo"),
 "AC-11":("correcoes-unit-final.xml","Guardas de metadados; scan de segredos locais executado sem correspondências"),
 "AC-12":("correcoes-isolated/multi-model-proposal.json","Duas versões reais contribuíram para90 linhas; stack de teste depois resetada"),
 "AC-13":("preservation-after-correcoes.json","Modelo v8, run e90linhas anteriores preservados após rebuild"),
 "AC-14":("ci-correcoes.json","CI Linux limpo passou,59testes,notebooks01/02"),
 "AC-15":("correcoes-isolated/model-benchmark.json","30treinos11.00s;500identidades0.34s;500treinos não executados"),
 "AC-16":("catalog-smoke.json","00–09 disponíveis;04/07 opt-in não acionado; scheduler05 NOT_IMPLEMENTED"),
 "AC-17":("reset-preview-proof.json","Hashes antes/depois idênticos; nenhum dado removido"),
 "AC-18":("correcoes-unit-final.xml","Recusa ambiente/labels/escopo/semfrase/planomodificado/obsoleto"),
 "AC-19":("correcoes-isolated/reset-independent-proof.json","Factory-reset/demo-ready e reset-data/empty isolados; SDK/API/SQL/S3/filas conferidos"),
 "AC-20":("workspace-after-correcoes.json","Original do usuário preservado; planos/resultados conferem hashes de.env/notebooks/backups"),
}
ci=dict(commit=base["tested_commit"],run_id=41847743558,job_id=126635599494,status="PASS",
        url="https://github.com/Quanticoi/marista-horas-intel-poc-ia/actions/runs/41847743558",
        tests_passed=59,notebooks=["01","02"],artifact_id=13332800707)
(REPORTS/"ci-correcoes.json").write_text(json.dumps(ci,indent=2),encoding="utf-8")
for test_id,(path,note) in evidence.items():
    assert (REPORTS/path).is_file(),path
    context=dict(base)
    if test_id in ("AC-12","AC-15","AC-19"):
        context.update(execution_id=None,run_id=None,model_name=None,model_version=None,snapshot_id=None,proposal_id=None)
    tests.append(dict(context,test_id=test_id,status="PASS",evidence=path,limitation=note))
result=dict(context=base,tests=tests,ci=ci,limitations=[
    "Contrato provisório; não homologa237regras V4.4 nem integra fontes institucionais",
    "Scheduler persistente/retry/checkpoint de campanhas05 NOT_IMPLEMENTED; incremento permitido pela spec",
    "500identidades não são500treinos/modelos registrados/APIs/modelos carregados",
    "Aprovação/publicação/revisão humana não exercitadas pelo catálogo de leitura",
    "Reset destrutivo somente na stack descartável; nenhum reset executado no projeto marista",
    "Revisão final do bootstrap PowerShell mantém PROPOSAL_ID vazio; sintaxe verificada localmente" ])
(REPORTS/"correcoes-v1.1-acceptance.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
lines=["# Correções v1.1 — relatório de execução", "",f"UTC: {base['timestamp_utc']}. Branch development. Código validado no CI: `{base['tested_commit']}`.",
 "", "## Entrega por fase", "",
 "| Fase | Implementação e evidência |", "|---|---|",
 "| A | Inventário, V3/V4.4 consultados e matriz: correcoes-fase-a-2026-11-04.md |",
 "| B | src/common/lineage.py: identidade tipada, hashes canônicos e manifests condicionais |",
 "| C | Migration005: grafo, N:N, evidência de contrato, vista/índices/backfill parcial |",
 "| D | Tags MLflow/Registry, inference_id, traces, atribuição por linha e manifests S3 |",
 "| E | Pydantic/JSON Schema poc-planilha-turmas-v1, application-view e lookup autenticados |",
 "| F | Notebooks00–09, distribuição sem clobber, controlador externo de reset e wrappers |",
 "| G |30treinos reais e500identidades medidos; scheduler persistente permanece pendente |",
 "| H | README, LINEAGE, contrato, cobertura funcional, operação/reset e ADR009 |",
 "| I |59testes locais/CI,19checksHTTP,notebooks,preservação e resetsisolados |",
 "", "## Resultado principal", "",
 f"Proposta `{journey['execution_id']}`; run `{journey['run_id']}`; experimento4; modelo `{journey['model_name']}` v{journey['model_version']}.",
 f"1050 registros SQL →90linhas DRAFT/API. MAE {journey['metrics']['mae']:.6f}; RMSE {journey['metrics']['rmse']:.6f}. Métricas DEMO.",
 f"[Run MLflow]({journey['run_url']}) · [CI aprovado]({ci['url']}).",
 "", "## Matriz de aceite", "", "| Teste | Estado | Evidência / limite |", "|---|---|---|"]
for test in tests:
    lines.append(f"| {test['test_id']} | {test['status']} | [{test['evidence']}]({test['evidence']}) — {test['limitation']} |")
lines += ["", "PASS do catálogo05 significa consulta executável; não significa scheduler implementado.",
 "", "## Operar e abrir os notebooks", "",
 "```powershell", ".\\deployment\\scripts\\compose.ps1 start", ".\\deployment\\scripts\\compose.ps1 journey", ".\\deployment\\scripts\\compose.ps1 test", "```",
 "Jupyter http://localhost:8888; MLflow5000; API8000/docs; inferência8001/docs; RustFS9001; dashboard8088.",
 "A cópia editada foi preservada (SHA256 AB37343F32483440DB03F8598617761E4A64A4EB24034FDBC50A4C3902614533).",
 "Abra `01_jornada_completa_planilha_turmas.update-eeacc6e47d5c.ipynb` para a jornada atualizada e use Restart Kernel and Run All.",
 "No02 informe explicitamente o proposal_id acima. Todos os notebooks foram confirmados writable=true pela API Jupyter.",
 "", "## Persistência", "",
 "planejamento_db/planning: dados sintéticos, propostas/linhas, auditoria, modelos operacionais e lineage. mlflow_db: metadados administrados pelo MLflow. RustFS/pucpr-poc: mlflow/, snapshots/, lineage/. Workspace é bind mount preservado.",
 "", "## Diagnóstico CI e comandos efetivamente executados", "",
 "1. Falha original reproduzida em volumes novos: `mlflow db upgrade` → UndefinedTable metrics. SDK MLflow inicializa o schema novo antes do upgrade; nenhuma migration própria do MLflow.",
 "2. CI41846141084 passou provisioning e falhou ao gravar relatório644 do checkout. Permissão da pasta de relatórios corrigida; CI41847743558 passou integralmente.",
 "```powershell",
 "python dev/validate_static.py",
 "python dev/generate_compose.py --check",
 "python deployment/scripts/build_journey_notebook.py --check",
 "docker compose build mlflow jupyter",
 "docker compose run --rm --no-deps tools migrate",
 "docker compose up -d --wait --wait-timeout 300",
 ".\\deployment\\scripts\\compose.ps1 journey",
 ".\\deployment\\scripts\\compose.ps1 test",
 "docker compose exec -T jupyter /usr/local/bin/_entrypoint.sh python -m src.workbench.preservation_check",
 "docker compose exec -T jupyter /usr/local/bin/_entrypoint.sh python -m src.workbench.smoke_catalog --proposal-id 93519267-7809-4e64-9e04-a79b9fb03d40 --reset-plan-id ef831e6f-361e-4e60-9fcc-8a740ee61a61",
 "python dev/prove_preview.py",
 "python dev/check_evidence_secrets.py",
 "```",
 "Ensaios isolados usaram `docker compose --env-file .env -f .runtime/correcoes-isolated/compose.json` com módulos execute_journey, benchmark e multi_model_proof. Relatórios preservados em correcoes-isolated/. Containers de teste foram parados; os da POC principal permanecem disponíveis.",
 "", "Reset foi chamado exclusivamente com project=marista-correcoes-isolated, --execute, frase forte e planos8479badb-3529-4e07-b94f-88355fe8a25a(factory/demo-ready) e344098cc-fa0d-4241-b357-6aafc2e94d3e(data/empty). Veja planos/resultados em reset/. Não reproduza esses comandos no projeto principal.",
 "", "## Limites e próximos incrementos", ""]
lines += ["- "+item for item in result["limitations"]]
(REPORTS/"correcoes-v1.1-acceptance.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print("Acceptance report consolidated from observed evidence")
