import html
from urllib.parse import urlencode
import mlflow
from src.workbench.operations_sdk import call
from src.operations.training import trace_for
from src.workbench.verification import verify_model_storage

def inspect_graph(cfg,kind,external_id,version="",limit=100,offset=0):
    graph=call(cfg,"GET","/v1/lineage/graph?"+urlencode(dict(kind=kind,external_id=external_id,version=version,limit=limit,offset=offset)))
    mlflow.set_tracking_uri(cfg.tracking);client=mlflow.MlflowClient();checks=[]
    for node in graph["nodes"]:
        check=dict(kind=node["entity_type"],id=node["external_id"],status="VERIFIED",evidence="PostgreSQL lineage entity")
        try:
            if node["entity_type"]=="model":
                name,number=node["external_id"].rsplit("/",1)
                registered=client.get_model_version(name,number)
                trace=trace_for(client,registered)
                proof=verify_model_storage(trace)
                if registered.run_id!=node["attributes"].get("run_id") or trace["artifact_sha256"]!=next(p["sha256"] for p in proof if p["key"].endswith("/model.pkl")):
                    raise ValueError("Mapping/hash mismatch")
                check.update(evidence=proof,url=f"{cfg.ui}/#/experiments/{trace['experiment_id']}/runs/{trace['run_id']}")
            elif node["entity_type"]=="run":
                run=client.get_run(node["external_id"])
                check["url"]=f"{cfg.ui}/#/experiments/{run.info.experiment_id}/runs/{run.info.run_id}"
            elif node["entity_type"]=="proposal":
                call(cfg,"GET",f"/v1/proposals/{node['external_id']}/application-view?limit=1")
                # The append-only proposal flag is RECORDED, never live proof.
                # Consult the cross-system verifier instead of trusting a stored label.
                verified=call(cfg,"GET",f"/v1/audit/proposal/{node['external_id']}")
                check["status"]=verified["status"]
                check["evidence"]={"proposal_id":node["external_id"],"live_audit_status":verified["status"]}
                check["url"]=f"http://localhost:8000/v1/proposals/{node['external_id']}/application-view"
            elif node["entity_type"]=="snapshot":
                from src.workbench.sdk import intake
                snapshot=intake("GET",f"/v1/datasets/{node['external_id']}")
                check["evidence"]={"snapshot_sha256":snapshot["sha256"],"verification":"intake verifies SQL + snapshot manifest/gold bytes"}
        except KeyError:
            check.update(status="LEGACY_PARTIAL",evidence="Legacy version lacks hash metadata")
        except ValueError:
            check.update(status="MISMATCH",evidence="Hash or mapping differs")
        except Exception as error:
            check.update(status="MISSING",evidence=type(error).__name__)
        checks.append(check)
    return dict(graph,checks=checks)

def render_graph(graph):
    names={n["entity_id"]:n["entity_type"]+": "+n["external_id"] for n in graph["nodes"]}
    rows="".join("<tr><td>"+html.escape(names.get(e["parent_id"],e["parent_id"]))+"</td><td> → "+html.escape(e["relation_type"])+" → </td><td>"+html.escape(names.get(e["child_id"],e["child_id"]))+"</td></tr>" for e in graph["edges"])
    links="".join('<li><a target="_blank" rel="noopener" href="'+html.escape(c["url"],quote=True)+'">'+html.escape(c["kind"]+": "+c["id"])+"</a> — "+c["status"]+"</li>" for c in graph["checks"] if c.get("url"))
    return "<h3>Snapshot → run → modelo → inferência → proposta</h3><table>"+rows+"</table><ul>"+links+"</ul><p>Objetos e hashes: tabela de evidências. Console RustFS: http://localhost:9001.</p>"
