"""Deterministic notebook source generator (does not run services on host)."""
import json
import ast
import sys
from pathlib import Path

cells = []


def section(title, objective, code, expected):
    cells.append(dict(cell_type="markdown", metadata={}, source=[f"## {title}\n\n{objective}\n\n**Esperado/evidência:** {expected}\n"]))
    cells.append(dict(cell_type="code", metadata={}, execution_count=None, outputs=[], source=code.strip().splitlines(keepends=True)))


cells.append(dict(cell_type="markdown", metadata={}, source=["# Jornada completa — Planilha Turmas (DEMO)\n\nExecute **Restart Kernel and Run All**. Dados sintéticos reproduzíveis (seed 42), sem fonte institucional. Métricas demonstram integração, não qualidade real. O grão é curso/período/disciplina/ciclo. A demanda histórica do período é atribuída às disciplinas pela regra provisória da POC; não é decisão funcional aprovada do MER.\n\nO notebook abre SQL com usuário de leitura; usa MLflow remoto em proxy, recarrega uma versão explícita e grava uma proposta DRAFT em transação. Não promove modelos. Cada Run All cria uma nova execução; repetir apenas a persistência com o mesmo conteúdo é idempotente.\n"]))
section("1. Configurações e dependências", "Testar SQL de origem/destino, versão do SDK/servidor, tracking real e upload/download pelo proxy antes de qualquer fit.", '''
import os, uuid, time, json
from pathlib import Path
import pandas as pd
import numpy as np
import httpx
import mlflow
import mlflow.sklearn
from IPython.display import display, Markdown
from src.workbench.journey_config import Settings
from src.workbench.journey_steps import dependencies, require_dependencies, step
from src.common.tracing import configure_tracing, trace_headers, trace_evidence
from src.workbench.verification import verify_model_storage, verify_proposal_sql
cfg = Settings.load()
execution_id = str(uuid.uuid4())
statuses = []
checks = dependencies(cfg, execution_id)
display(pd.DataFrame(checks))
require_dependencies(checks, cfg)
experiment_id = configure_tracing(cfg)
display({"experiment":cfg.experiment,"experiment_id":experiment_id,"model_name":cfg.model_name})
statuses.append(dict(stage="dependencies", status="PASS"))
display({"execution_id":execution_id, "mode":cfg.mode, "tracking":cfg.tracking})
''', "Tabela PASS; se houver FAIL o notebook interrompe com diagnóstico, sem tracking local.")
section("2. Extração SQL versionada", "A conexão é aberta por src.data.journey usando SOURCE_DATABASE_URL. Fonte DEMO: planejamento_db.planning.historical_enrollments e catálogo relacionado. O seed já foi carregado no bootstrap.", '''
from src.data.journey import extract, prepare, FEATURES, TARGET, QUERY
with step("SQL extraction", execution_id, statuses):
    history, snapshot = extract(cfg)
    display(Markdown("```sql\\n" + QUERY.read_text() + "\\n```"))
    display({"source":"planejamento_db/planning/SYNTHETIC", "cycle":cfg.cycle,
        "course":cfg.course or "all", "snapshot":snapshot, "rows":len(history),
        "nulls":int(history.isna().sum().sum()), "duplicates":int(history.duplicated().sum())})
    display(history.dtypes.astype(str).rename("type").to_frame())
    display(history.head())
''', "Consulta parametrizada, snapshot/hash, filtros, contagens, tipos e amostra sem credenciais.")
section("3. Preparação temporal", "Reservar o último semestre histórico para avaliação. O conjunto de proposta contém somente chaves acadêmicas e o próximo semestre, sem alvo. Transformações serão ajustadas exclusivamente no treino.", '''
with step("prepare", execution_id, statuses):
    train, evaluation, future = prepare(history, snapshot)
    display(pd.DataFrame([
        {"dataset":"train", "rows":len(train), "start":int(train.semester_index.min()), "end":int(train.semester_index.max())},
        {"dataset":"evaluation", "rows":len(evaluation), "start":int(evaluation.semester_index.min()), "end":int(evaluation.semester_index.max())},
        {"dataset":"proposal", "rows":len(future), "start":int(future.semester_index.min()), "end":int(future.semester_index.max())}]))
''', "Treino < avaliação < proposta no tempo.")
section("4. Modelo e métricas", "Ridge(alpha=1, seed=42), one-hot de curso/período/disciplina e padronização temporal. Alvo: estudantes do período atribuídos à disciplina. MAE mede erro absoluto médio; RMSE penaliza mais os erros grandes. Ambas em estudantes.", '''
from src.training.journey import estimator, evaluate, SEED
with step("model and metrics", execution_id, statuses):
    model = estimator()
    display({"features":FEATURES, "target":TARGET, "seed":SEED, "metrics":["MAE", "RMSE"]})
    display(model)
''', "Pipeline instanciado e funções de avaliação definidas antes do fit.")
section("5. Experimento e execução", "Criar/recuperar o experimento proxy e registrar identidade da extração, query, código, features e referência sintética. Cada etapa posterior encerra a run como FAILED se ocorrer erro.", '''
from src.mlops.journey import start, register
with step("tracking", execution_id, statuses):
    trace = start(cfg, execution_id, snapshot, history)
    display(trace)
    display(Markdown(f"[Abrir execução no MLflow]({trace['run_url']})"))
''', "experiment_id/run_id e link clicável; CSV de referência e SQL enviados pelo proxy.")
section("6. Treinamento e avaliação", "Executar fit/predict reais. O modelo persistido é exatamente o avaliado; não há retreino oculto com o conjunto de avaliação.", '''
if mlflow.active_run() is None or mlflow.active_run().info.run_id != trace["run_id"]:
    raise RuntimeError("Treinamento exige a run desta jornada ativa. Para novo treino, execute desde a primeira etapa.")
with step("fit and evaluate", execution_id, statuses):
    started = time.monotonic()
    model.fit(train[FEATURES], train[TARGET])
    predicted = model.predict(evaluation[FEATURES])
    metrics = evaluate(evaluation[TARGET], predicted)
    mlflow.log_metrics({**metrics, "training_seconds":time.monotonic()-started})
    mlflow.log_dict({"actual":evaluation[TARGET].tolist(), "predicted":predicted.tolist()}, "evaluation.json")
    display(metrics)
''', "MAE/RMSE calculados e registrados; métricas DEMO não comprovam qualidade institucional.")
section("7. Persistência do modelo e Registry", "O SDK envia modelo, transformações, assinatura e exemplo ao MLflow; somente o servidor grava o RustFS. A versão será selecionada explicitamente para teste DRAFT, sem alias champion.", '''
with step("register", execution_id, statuses):
    trace = register(cfg, globals().get("model"), train[FEATURES].head(3), trace, execution_id)
    mlflow.end_run(status="FINISHED")
    display(trace)
    globals().pop("model", None)  # Infer?ncia recarrega a vers?o persistida.
''', "Nome, versão, URI e run; objeto treinado removido da memória.")
section('7b. Conferir o modelo no Object Store', 'Leitura independente no RustFS e pelo proxy MLflow, sem gravar uma segunda c?pia. **Esperado:** bytes e SHA256 id?nticos para modelo, assinatura e depend?ncias; bucket/chave exibidos. Pode repetir esta verifica??o.\n', 'with step("verify Object Store", execution_id, statuses):\n    storage_evidence = verify_model_storage(trace)\n    display(pd.DataFrame(storage_evidence))\n', "PASS; evid?ncia exibida.")
section("8. Recarregar e inferir no serviço existente", "Baixar a versão registrada e executar predict no conjunto futuro. Chamar também o serviço inference: ele carrega a mesma versão e verifica run/execução/snapshot. Registro não significa promoção operacional.", '''
from src.inference.journey import load_version
from src.common.settings import required
with step("reload and inference", execution_id, statuses):
    restored, registered = load_version(trace["model_name"], trace["model_version"], trace["run_id"], execution_id)
    predictions = restored.predict(future[FEATURES])
    response = httpx.post(cfg.inference + "/internal/draft/predict", timeout=120,
        headers={"Authorization":"Bearer " + required("INFERENCE_TOKEN"), "X-Correlation-ID":execution_id, **trace_headers()},
        json={"execution_id":execution_id, "snapshot_id":snapshot["id"], "model_name":trace["model_name"],
              "model_version":trace["model_version"], "run_id":trace["run_id"], "records":future[FEATURES].to_dict("records")})
    response.raise_for_status()
    inference = response.json()
    trace["inference_id"] = inference["inference_id"]
    trace["artifact_sha256"] = next(item["sha256"] for item in storage_evidence if item["key"].endswith("/model.pkl"))
    assert inference["model_version"] == trace["model_version"] and inference["run_id"] == trace["run_id"]
    np.testing.assert_allclose(predictions, inference["predictions"], rtol=1e-10)
    client = mlflow.MlflowClient()
    client.log_metric(trace["run_id"], "inference_rows", len(predictions))
    client.log_metric(trace["run_id"], "inference_seconds", inference["duration_seconds"])
    display({k:v for k,v in inference.items() if k != "predictions"})
    display(future.assign(forecast_raw=predictions).head())
''', "Download real do artefato; serviço carregou versão igual e produziu previsões iguais.")
section("9. Compor Planilha Turmas", "Regra provisória POC: estudantes propostos = max(0, ceil(previsão)); turmas = ceil(estudantes/capacidade). Capacidade demonstrativa = 40. Zero demanda gera zero turmas. Sem ajustes humanos nesta execução.", '''
from src.persistence.journey import compose, persist, RULE
with step("compose proposal", execution_id, statuses):
    capacity = 40
    lines = compose(future, predictions, capacity)
    display({"rule":RULE, "capacity":capacity, "state":"DRAFT"})
    display(pd.DataFrame(lines).head())
''', "Valor previsto, estudantes propostos, turmas e ajuste humano separados.")
section("10. Persistir e verificar idempotência", "Gravar cabeçalho e todas as linhas numa transação PostgreSQL em planejamento_db.planning.proposal_*. Repetição idêntica retorna a geração existente; conteúdo diferente com o mesmo UUID é rejeitado. Novo Run All preserva as versões anteriores.", '''
with step("persist and idempotency", execution_id, statuses):
    generation = persist(cfg, execution_id, snapshot, trace, lines, capacity)
    repeated = persist(cfg, execution_id, snapshot, trace, lines, capacity)
    assert generation["execution_id"] == repeated["execution_id"]
    assert generation["row_count"] == len(lines)
    from src.persistence.lineage import publish_manifest
    lineage_manifest = publish_manifest(cfg, execution_id)
    display(lineage_manifest)
    display(generation)
''', "Geração DRAFT persistida com vínculos SQL/run/modelo/regra; repetição sem duplicações.")
section('10b. Conferir a proposta diretamente no PostgreSQL', 'Nova conex?o com APPLICATION_DATABASE_URL, ap?s o commit. Banco de neg?cio planejamento_db, tabelas planning.proposal_generations e planning.proposal_lines. **Esperado:** todas as linhas e valores iguais ? proposta, com run e vers?o corretas. Consulta versionada em sql/queries/verify_proposal.sql; esta etapa somente l?.\n', 'with step("verify proposal SQL", execution_id, statuses):\n    database_evidence = verify_proposal_sql(cfg, execution_id, trace, lines)\n    display(database_evidence)\n', "PASS; evid?ncia exibida.")
section("11. Consultar API e reconciliar", "A API consulta PostgreSQL sem treinamento. Comparar todas as linhas e rastreabilidade com a proposta escrita pelo notebook.", '''
with step("API reconciliation", execution_id, statuses):
    headers = {"Authorization":"Bearer " + required("API_TOKEN"), "X-Correlation-ID":execution_id, **trace_headers()}
    def get_api(path):
        r = httpx.get(cfg.api + path, headers={**headers, **trace_headers()}, timeout=cfg.timeout)
        r.raise_for_status()
        return r.json()
    api_generation = get_api(f"/v1/proposals/{execution_id}")
    api_lines = get_api(f"/v1/proposals/{execution_id}/lines?limit=500")
    assert api_generation["run_id"] == trace["run_id"]
    assert api_generation["model_version"] == trace["model_version"]
    assert len(api_lines) == len(lines) == api_generation["row_count"]
    expected = {tuple(r[k] for k in ["course_id","period_id","discipline_id"]):r for r in lines}
    for row in api_lines:
        original = expected[tuple(row[k] for k in ["course_id","period_id","discipline_id"])]
        assert row["proposed_students"] == original["proposed_students"]
        assert row["proposed_groups"] == original["proposed_groups"]
        assert row["forecast_raw"] == original["forecast_raw"]
    display(api_generation)
    display(pd.DataFrame(api_lines).head())
''', "Mesmos IDs, quantidades e total no SQL e na API; run ligada à geração.")
section("12. Evidências finais", "Salvar resumo reproduzível da execução no workspace e no MLflow. Consultar dashboard pelo correlation_id.", '''
tracing = trace_evidence(cfg, statuses, trace, execution_id)
display(pd.DataFrame(tracing))
summary = {"execution_id":execution_id, "mode":cfg.mode, "sql_rows":len(history), "metrics":metrics,
    **trace, "proposal_id":execution_id, "persisted_rows":len(lines), "api_rows":len(api_lines),
    "snapshot_id":snapshot["id"], "dataset_sha256":snapshot["dataset_sha256"], "stages":statuses, "traces":tracing, "storage_evidence":storage_evidence, "database_evidence":database_evidence}
reports = Path("/workspace/reports")
reports.mkdir(parents=True, exist_ok=True)
report = reports / f"journey-{execution_id}.json"
report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
mlflow.MlflowClient().log_artifact(trace["run_id"], str(report), "evidence")
display(pd.DataFrame(statuses))
display(summary)
display(Markdown(f"[Run MLflow]({trace['run_url']}) · [API](http://127.0.0.1:8000/docs) · [Dashboard](http://127.0.0.1:8088) · [RustFS](http://127.0.0.1:9001)"))
''', "Todas as etapas PASS, evidência local e no Artifact Store, links sem segredos.")

notebook = dict(cells=cells, metadata={"kernelspec":{"display_name":"PUCPR Python 3.12", "language":"python", "name":"pucpr"},
    "language_info":{"name":"python", "version":"3.12.9"}}, nbformat=4, nbformat_minor=5)
for i, cell in enumerate(cells):
    cell["id"] = f"journey-{i:02d}"
root = Path(__file__).resolve().parents[2]
if "--check" in sys.argv:
    existing = json.loads((root / "notebooks/01_jornada_completa_planilha_turmas.ipynb").read_text(encoding="utf-8"))
    def code_trees(items):
        return [ast.dump(ast.parse("".join(c["source"]))) for c in items if c["cell_type"] == "code"]
    assert code_trees(existing["cells"]) == code_trees(cells), "Notebook code differs from generator"
    print("PASS notebook generator code matches principal notebook")
    sys.exit(0)
(root / "notebooks/01_jornada_completa_planilha_turmas.ipynb").write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
