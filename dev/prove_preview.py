"""Non-destructive proof that reset preview does not change persistent inventory."""
import importlib.util
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("reset_poc",root/"deployment/scripts/reset_poc.py")
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
before=module.data_inventory("marista")
plan=module.preview("poc","marista","reset-data")
after=module.data_inventory("marista")
assert before==plan["inventory"]==after
(root/"artifacts/reports/reset-preview-proof.json").write_text(json.dumps(dict(test_id="AC17",status="PASS",
    plan_id=plan["plan_id"],before_hash=module.digest(before),after_hash=module.digest(after)),indent=2),encoding="utf-8")
print("PASS preview: persistent inventory unchanged; plan_id="+plan["plan_id"])
