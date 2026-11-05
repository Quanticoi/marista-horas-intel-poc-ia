"""Versioned metric selection and pooled errors; no model training or API calls."""
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
IMPLEMENTED = {"mae", "rmse", "medae", "wape", "smape", "r2", "bias", "absolute_error_p90"}


def catalog(path=None):
    return json.loads((path or ROOT / "config/metric_catalog.yaml").read_text(encoding="utf-8"))


def profile(name):
    if name not in {"forecast_baseline", "forecast_extended", "academic_impact", "compute_resource"}:
        raise ValueError("Unknown metric profile")
    return json.loads((ROOT / "config/metric_profiles" / (name + ".yaml")).read_text(encoding="utf-8"))


def evaluate(actual, predicted, selected, task_type="regression"):
    definitions = {m["metric_id"]: m for m in catalog()["metrics"]}
    if len(selected) != len(set(selected)):
        raise ValueError("Duplicate metric selection")
    for metric in selected:
        if metric not in definitions or definitions[metric]["task_type"] != task_type:
            raise ValueError("Unknown or incompatible metric: " + metric)
    y, p = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if y.ndim != 1 or y.shape != p.shape or not len(y) or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("Expected matching nonempty finite 1D actual/prediction arrays")
    error = p-y
    absolute = np.abs(error)
    denominator = float(np.abs(y).sum())
    variance = float(np.square(y-y.mean()).sum())
    smape_denominator = np.abs(y)+np.abs(p)
    smape_terms = np.divide(2*absolute, smape_denominator, out=np.zeros_like(y), where=smape_denominator > 0)
    values = dict(mae=float(absolute.mean()), rmse=float(np.sqrt(np.square(error).mean())),
                  medae=float(np.median(absolute)), bias=float(error.mean()),
                  absolute_error_p90=float(np.quantile(absolute, .9)), smape=float(100*smape_terms.mean()))
    reasons = {}
    if denominator > 0:
        values["wape"] = float(100*absolute.sum()/denominator)
    else:
        reasons["wape"] = "ZERO_ABSOLUTE_ACTUAL_SUM"
    if len(y) >= 2 and variance > 0:
        values["r2"] = float(1-np.square(error).sum()/variance)
    else:
        reasons["r2"] = "INSUFFICIENT_OR_CONSTANT_ACTUAL"
    return {m: dict(status="EVALUATED" if m in values else "NOT_EVALUATED",
                    value=values.get(m), reason=reasons.get(m)) for m in selected}


def aggregate(records, selected):
    """Pool observations only inside identical task/target/horizon/split/data-class."""
    groups = {}
    keys = ("task_type", "target_name", "horizon", "split_id", "data_class")
    for record in records:
        if any(not record.get(k) for k in keys):
            raise ValueError("Missing comparison identity")
        key = tuple(record[k] for k in keys)
        groups.setdefault(key, []).append(record)
    result = []
    for key, members in groups.items():
        for member in members:
            evaluate(member["actual"], member["predicted"], selected, key[0])
        actual = np.concatenate([m["actual"] for m in members])
        predicted = np.concatenate([m["predicted"] for m in members])
        result.append(dict(comparison=dict(zip(keys, key)), count=len(actual), models=len(members),
                           aggregation="POOLED_OBSERVATIONS", metrics=evaluate(actual, predicted, selected, key[0])))
    return result
