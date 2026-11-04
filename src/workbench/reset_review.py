"""Read-only notebook companion to the external destructive controller."""
import json
from pathlib import Path

def review_plan(params):
    mode="reset-data" if params.reset_mode=="preview" else params.reset_mode
    result=dict(state="PREVIEW_REQUIRED",commands={
        "preview":f"python deployment/scripts/reset_poc.py preview --environment poc --project marista --mode {mode}",
        "execution":"Use the external controller with a fresh plan, --execute and the exact confirmation phrase. Never execute from this notebook.",
        "reinitialize":params.reinitialize},risks=["Data deletion is irreversible without separately maintained backups","Factory reset stops this kernel"],
        destructive_execution="NOT_EXECUTED")
    if params.reset_plan_id:
        root=Path("/reports/reset");plan=root/(str(params.reset_plan_id)+".plan.json")
        if not plan.exists():
            raise ValueError("Plan not found: generate preview on host and select its UUID")
        document=json.loads(plan.read_text())
        result.update(state="PLAN_AVAILABLE",plan_id=str(params.reset_plan_id),inventory=document.get("inventory",{}),
            protected_files=document.get("preserved",{}),plan=document)
        project=document["scope"]["project"]
        result["commands"]["execution"]=f"python deployment/scripts/reset_poc.py execute --environment poc --project {project} --plan-id {params.reset_plan_id} --execute --reinitialize {params.reinitialize}"
        executed=root/(str(params.reset_plan_id)+".result.json")
        if executed.exists():
            result["result"]=json.loads(executed.read_text())
    return result
