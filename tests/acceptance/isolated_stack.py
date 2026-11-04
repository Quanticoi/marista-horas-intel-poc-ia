"""Create a separate Compose project for clean-start acceptance; never delete it."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
directory = ROOT / ".runtime" / "correcoes-isolated"
directory.mkdir(parents=True, exist_ok=True)
document = json.loads((ROOT / "compose.yaml").read_text())
document["name"] = "marista-correcoes-isolated"
document["networks"] = {"default": {"ipam": {"config": [{"subnet": "10.254.241.0/24"}]}}}
for name, service in document["services"].items():
    service.setdefault("environment",{})["POC_ISOLATED_TESTS"]="1"
    service["environment"]["POC_PROJECT"]="marista-correcoes-isolated"
    service.pop("ports", None)
    service.pop("build", None)
    mounts = []
    for mount in service.get("volumes", []):
        if mount.startswith("./"):
            host, target, *options = mount.split(":")
            path = directory / host.removeprefix("./")
            path.mkdir(parents=True, exist_ok=True)
            mounts.append({"type": "bind", "source": str(path), "target": target,
                           "read_only": "ro" in options})
        else:
            mounts.append(mount)
    if mounts:
        service["volumes"] = mounts
    if name not in ("postgres","rustfs","rabbitmq","volume-tools"):
        for folder in ("src","sql","notebooks","tests"):
            service.setdefault("volumes",[]).append({"type":"bind","source":str(ROOT/folder),"target":"/app/"+folder,"read_only":True})
(directory / "compose.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
print("Isolated project configured: marista-correcoes-isolated (no host ports)")
