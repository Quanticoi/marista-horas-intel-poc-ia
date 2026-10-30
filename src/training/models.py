"""Temporal evaluation uses expanding windows and exact semester lags."""
import math
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge


def metrics(actual, predicted):
    a, p = np.asarray(actual), np.asarray(predicted)
    denominator = np.abs(a) + np.abs(p)
    return {"mae": float(np.mean(np.abs(a-p))),
            "rmse": float(np.sqrt(np.mean((a-p)**2))),
            "smape": float(np.mean(np.divide(200*np.abs(a-p), denominator,
                out=np.zeros_like(a, dtype=float), where=denominator != 0)))}


def features(history, target):
    return [target, target % 2, history[target-1], history[target-2]]


def forecast(history, target, algorithm):
    if not history or target <= max(history):
        raise ValueError("Target must follow training history")
    if algorithm == "seasonal" or target-1 not in history or target-2 not in history:
        same_season = [t for t in history if t % 2 == target % 2]
        return float(history[max(same_season or history)])
    indices = [t for t in sorted(history) if t-1 in history and t-2 in history]
    if len(indices) < 4:
        return forecast(history, target, "seasonal")
    model = Ridge(alpha=1.0) if algorithm == "ridge" else RandomForestRegressor(
        n_estimators=40, max_depth=3, random_state=42, n_jobs=1)
    model.fit([features(history, t) for t in indices], [history[t] for t in indices])
    return max(0.0, float(model.predict([features(history, target)])[0]))


def select(history):
    points = sorted(history)
    fallback = len(points) < 8
    algorithms = ["seasonal"] if fallback else ["seasonal", "ridge", "forest"]
    results = {}
    for algorithm in algorithms:
        actual, predicted = [], []
        for index in range(max(2, len(points)-4), len(points)):
            past = {t: history[t] for t in points[:index]}
            actual.append(history[points[index]])
            predicted.append(forecast(past, points[index], algorithm))
        results[algorithm] = metrics(actual, predicted) if actual else None
    winner = min(algorithms, key=lambda a: results[a]["mae"] if results[a] else math.inf)
    return winner, results, fallback
