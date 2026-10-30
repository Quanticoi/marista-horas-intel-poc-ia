"""Fitted, serializable forecasting pipeline. predict never fits an estimator."""
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from src.training.models import features


class SemesterForecaster(RegressorMixin, BaseEstimator):
    def __init__(self, algorithm="seasonal"):
        self.algorithm = algorithm

    def fit(self, history, y=None):
        if self.algorithm not in ("seasonal", "ridge", "forest") or not history:
            raise ValueError("Unsupported algorithm or empty history")
        self.history_ = {int(k): float(v) for k, v in history.items()}
        self.model_ = None
        indices = [t for t in sorted(self.history_) if t-1 in self.history_ and t-2 in self.history_]
        if self.algorithm != "seasonal" and len(indices) >= 4:
            self.model_ = Ridge(alpha=1.0) if self.algorithm == "ridge" else RandomForestRegressor(
                n_estimators=40, max_depth=3, random_state=42, n_jobs=1)
            self.model_.fit([features(self.history_, t) for t in indices], [self.history_[t] for t in indices])
        self.is_fitted_ = True
        return self

    def predict(self, frame):
        if list(frame.columns) != ["target_year", "target_semester"]:
            raise ValueError("Expected target_year and target_semester")
        result = []
        for year, semester in frame.itertuples(index=False, name=None):
            if year != int(year) or not 2000 <= year <= 2200 or semester not in (1, 2):
                raise ValueError("Invalid target")
            target = int(year) * 2 + int(semester) - 1
            if target <= max(self.history_):
                raise ValueError("Target must follow training history")
            if self.model_ is None or target-1 not in self.history_ or target-2 not in self.history_:
                same = [t for t in self.history_ if t % 2 == target % 2]
                value = self.history_[max(same or self.history_)]
            else:
                value = self.model_.predict([features(self.history_, target)])[0]
            if not np.isfinite(value):
                raise ValueError("Non-finite prediction")
            result.append(max(0.0, float(value)))
        return np.asarray(result)
