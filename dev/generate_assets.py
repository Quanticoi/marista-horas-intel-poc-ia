"""Authoring helper (stdlib only). Generates the retained Helm reference charts only.

Not used for local Compose deployment. Never rewrites notebooks.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path, value):
    path = ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2)+"\n", encoding="utf-8")


def obj(kind, name, namespace, spec=None, **extra):
    versions = {"Deployment":"apps/v1", "StatefulSet":"apps/v1", "CronJob":"batch/v1",
                "Job":"batch/v1", "NetworkPolicy":"networking.k8s.io/v1",
                "Role":"rbac.authorization.k8s.io/v1", "RoleBinding":"rbac.authorization.k8s.io/v1"}
    result = dict(apiVersion=versions.get(kind,"v1"), kind=kind,
                  metadata=dict(name=name, namespace=namespace, labels={"app.kubernetes.io/part-of":"pucpr-poc"}))
    if spec is not None:
        result["spec"] = spec
    return dict(result, **extra)


def service(name, ns, port, extra=None):
    ports = [dict(name="main",port=port,targetPort=port)]
    if extra:
        ports.append(dict(name="console",port=extra,targetPort=extra))
    return obj("Service",name,ns,dict(type="ClusterIP",selector={"app":name},ports=ports))


def pvc(name, ns, size):
    item = obj("PersistentVolumeClaim",name,ns,dict(accessModes=["ReadWriteOnce"],
        storageClassName="{{ .Values.storageClass }}",resources={"requests":{"storage":size}}))
    item["metadata"]["annotations"] = {"helm.sh/resource-policy":"keep"}
    return item


def container(name, image, command, port=None, secret=True, memory="1Gi", cpu="1"):
    result = dict(name=name,image=image,imagePullPolicy="IfNotPresent",command=command,
        resources=dict(requests={"cpu":"100m","memory":"128Mi"},limits={"cpu":cpu,"memory":memory}),
        securityContext=dict(allowPrivilegeEscalation=False,capabilities={"drop":["ALL"]}))
    if secret:
        result["envFrom"] = [{"configMapRef":{"name":"poc-config"}},{"secretRef":{"name":"poc-runtime"}}]
    if port:
        result["ports"]=[{"containerPort":port}]
        result["readinessProbe"]={"tcpSocket":{"port":port},"initialDelaySeconds":5,"periodSeconds":10}
        result["livenessProbe"]={"tcpSocket":{"port":port},"initialDelaySeconds":30,"periodSeconds":20}
        result["startupProbe"]={"tcpSocket":{"port":port},"failureThreshold":60,"periodSeconds":5}
    return result


def workload(name, ns, containers, stateful=False, volume=None, service_account=None):
    pod=dict(containers=containers,terminationGracePeriodSeconds=60,
             automountServiceAccountToken=bool(service_account),securityContext={"fsGroup":1000})
    if service_account:
        pod["serviceAccountName"]=service_account
    if volume:
        claim,mount=volume
        pod["volumes"]=[{"name":"storage","persistentVolumeClaim":{"claimName":claim}}]
        for item in containers:
            item["volumeMounts"]=[{"name":"storage","mountPath":mount}]
    spec=dict(replicas=1,selector={"matchLabels":{"app":name}},
              template={"metadata":{"labels":{"app":name,"app.kubernetes.io/part-of":"pucpr-poc"}},"spec":pod})
    if stateful:
        spec["serviceName"]=name
    else:
        spec["strategy"]={"type":"Recreate"} if volume else {"type":"RollingUpdate"}
    return obj("StatefulSet" if stateful else "Deployment",name,ns,spec)


def app_container(name, module, port=None, **kwargs):
    item=container(name,"{{ .Values.image }}",["python","-m",module],port,**kwargs)
    if port:
        item["command"]=["python","-m","uvicorn",module+":app","--host","0.0.0.0","--port",str(port),"--no-access-log"]
        item["readinessProbe"]={"httpGet":{"path":"/ready","port":port},"periodSeconds":10,"timeoutSeconds":15}
        item["livenessProbe"]={"httpGet":{"path":"/health","port":port},"periodSeconds":20}
    return item


def chart(name, ns, staged):
    write(f"deployment/helm/{name}/Chart.yaml", f"apiVersion: v2\nname: {name}\nversion: 0.1.0\nappVersion: '0.1.0'\ntype: application\n")
    values=dict(image="pucpr-poc:0.1.0",jupyterImage="pucpr-jupyter:0.1.0",storageClass="local-path",enabledStages=list(dict.fromkeys(s for s,_ in staged)),
                resources=[dict(stage=s,resource=r) for s,r in staged])
    write(f"deployment/helm/{name}/values.yaml", values)
    write(f"deployment/helm/{name}/templates/resources.yaml", """{{- range .Values.resources }}
{{- if has .stage $.Values.enabledStages }}
---
{{ tpl (toYaml .resource) $ }}
{{- end }}
{{- end }}
""")
    write(f"deployment/values/local/{name}.yaml", "storageClass: local-path\nimage: pucpr-poc:0.1.0\n")


def main():
    namespaces=["training","mlops","ai-service","data","operations"]
    write("deployment/kubernetes/namespaces/namespaces.json",dict(apiVersion="v1",kind="List",items=[
        {"apiVersion":"v1","kind":"Namespace","metadata":{"name":ns,"labels":{"app.kubernetes.io/part-of":"pucpr-poc"}}} for ns in namespaces]))
    policies=[]
    for ns in namespaces:
        policies.append(obj("NetworkPolicy","poc-only",ns,dict(podSelector={},policyTypes=["Ingress","Egress"],
            ingress=[{"from":[{"namespaceSelector":{"matchLabels":{"app.kubernetes.io/part-of":"pucpr-poc"}}}]}],
            egress=[{"to":[{"namespaceSelector":{"matchLabels":{"app.kubernetes.io/part-of":"pucpr-poc"}}}]},
                    {"to":[{"namespaceSelector":{"matchLabels":{"kubernetes.io/metadata.name":"kube-system"}}}],
                     "ports":[{"protocol":"UDP","port":53},{"protocol":"TCP","port":53}]}])))
    # Collector needs the API service/node address; only TCP/443 and TCP/6443, no public app endpoints.
    policies.append(obj("NetworkPolicy","collector-apiserver", "operations",dict(podSelector={"matchLabels":{"app":"dashboard"}},
        policyTypes=["Egress"],egress=[{"ports":[{"protocol":"TCP","port":443},{"protocol":"TCP","port":6443}]}])))
    write("deployment/kubernetes/networkpolicies/policies.json",dict(apiVersion="v1",kind="List",items=policies))
    roles=[obj("ServiceAccount","collector","operations")]
    for ns in namespaces:
        roles += [obj("Role","poc-observer",ns,rules=[{"apiGroups":[""],"resources":["pods","pods/log","persistentvolumeclaims","events"],"verbs":["get","list","watch"]}]),
            obj("RoleBinding","poc-observer",ns,roleRef={"apiGroup":"rbac.authorization.k8s.io","kind":"Role","name":"poc-observer"},
                subjects=[{"kind":"ServiceAccount","name":"collector","namespace":"operations"}])]
    write("deployment/kubernetes/rbac/collector.json",dict(apiVersion="v1",kind="List",items=roles))
    postgres=container("postgres","postgres:15.10-bookworm",["docker-entrypoint.sh","postgres"],5432,secret=False)
    # Official postgres entrypoint initializes/chowns the data directory before dropping to postgres.
    postgres.pop("securityContext")
    postgres["env"]=[{"name":"POSTGRES_PASSWORD","valueFrom":{"secretKeyRef":{"name":"poc-runtime","key":"POSTGRES_PASSWORD"}}},
                      {"name":"PGDATA","value":"/var/lib/postgresql/data/pgdata"}]
    rust=container("rustfs","rustfs/rustfs:1.0.0",["/usr/bin/rustfs","/data"],9000,secret=False,memory="2Gi")
    rust.pop("command")
    rust["args"]=["/data"]
    rust["env"]=[{"name":"RUSTFS_ACCESS_KEY","valueFrom":{"secretKeyRef":{"name":"poc-runtime","key":"AWS_ACCESS_KEY_ID"}}},
                 {"name":"RUSTFS_SECRET_KEY","valueFrom":{"secretKeyRef":{"name":"poc-runtime","key":"AWS_SECRET_ACCESS_KEY"}}},
                 {"name":"RUSTFS_CONSOLE_ENABLE","value":"true"},{"name":"RUSTFS_ADDRESS","value":":9000"},
                 {"name":"RUSTFS_CONSOLE_ADDRESS","value":":9001"}]
    rabbit=container("rabbitmq","rabbitmq:4.0.5-management",["docker-entrypoint.sh","rabbitmq-server"],5672,secret=False)
    rabbit.pop("securityContext")
    rabbit["env"]=[{"name":"RABBITMQ_DEFAULT_USER","value":"poc"},
                   {"name":"RABBITMQ_DEFAULT_PASS","valueFrom":{"secretKeyRef":{"name":"poc-runtime","key":"RABBITMQ_PASSWORD"}}}]
    staged=[]
    for name,c,port,extra,mount in [("postgres",postgres,5432,None,"/var/lib/postgresql/data"),
        ("rustfs",rust,9000,9001,"/data"),("rabbitmq",rabbit,5672,15672,"/var/lib/rabbitmq")]:
        staged += [(name,pvc(name,"data","5Gi")),(name,service(name,"data",port,extra)),
                   (name,workload(name,"data",[c],stateful=True,volume=(name,mount)))]
    chart("platform","data",staged)
    mlflow=container("mlflow","{{ .Values.image }}",["python","-m","src.common.launch","mlflow"],5000,memory="2Gi")
    mlflow["env"]=[{"name":"MLFLOW_WORKERS","value":"1"}]
    mlflow["resources"]["requests"]["memory"]="512Mi"
    mlflow_health={"path":"/health","port":5000,"httpHeaders":[{"name":"Host","value":"mlflow.mlops.svc.cluster.local:5000"}]}
    mlflow["startupProbe"]={"httpGet":mlflow_health,"failureThreshold":60,"periodSeconds":5,"timeoutSeconds":5}
    mlflow["readinessProbe"]={"httpGet":mlflow_health,"periodSeconds":10,"timeoutSeconds":5}
    monitor=app_container("monitoramento","src.monitoring.main",8010,memory="512Mi")
    monitor["envFrom"][1]={"secretRef":{"name":"poc-monitor"}}
    chart("mlops","mlops",[("mlflow",service("mlflow","mlops",5000)),("mlflow",workload("mlflow","mlops",[mlflow])),
        ("monitor",service("monitoramento","mlops",8010)),("monitor",workload("monitoramento","mlops",[monitor]))])
    jupyter=container("jupyter","{{ .Values.jupyterImage }}",["/usr/local/bin/_entrypoint.sh","python","-m","src.common.launch","jupyter"],8888,memory="3Gi",cpu="2")
    chart("training","training",[("app",pvc("workspace","training","5Gi")),("app",service("jupyter","training",8888)),
        ("app",workload("jupyter","training",[jupyter],volume=("workspace","/workspace")))])
    api=app_container("api","src.api.main",8000)
    inference=app_container("inference","src.inference.main",8001,memory="2Gi",cpu="2")
    inference["envFrom"][1]={"secretRef":{"name":"poc-inference"}}
    worker=container("worker","{{ .Values.image }}",["celery","-A","src.workers.tasks:app","worker","--loglevel=INFO","--concurrency=2"],memory="2Gi",cpu="2")
    worker["readinessProbe"]={"exec":{"command":["python","-m","src.common.cli","worker-ready"]},"periodSeconds":30,"timeoutSeconds":15}
    chart("ai-service","ai-service",[("app",service("inference","ai-service",8001)),("app",workload("inference","ai-service",[inference])),
        ("app",service("api","ai-service",8000)),("app",workload("api","ai-service",[api])),("app",workload("worker","ai-service",[worker]))])
    dashboard=app_container("dashboard","src.dashboard.main",8088)
    collector=app_container("collector","src.monitoring.collector",secret=False,memory="512Mi")
    chart("operations","operations",[("app",pvc("logs","operations","2Gi")),("app",service("dashboard","operations",8088)),
        ("app",workload("dashboard","operations",[dashboard,collector],volume=("logs","/logs"),service_account="collector"))])



if __name__ == "__main__":
    main()
