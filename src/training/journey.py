from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from src.data.journey import KEYS

SEED = 42


def estimator():
    return Pipeline([("features", ColumnTransformer([
        ("academic", OneHotEncoder(handle_unknown="ignore", sparse_output=False), KEYS),
        ("time", StandardScaler(), ["semester_index", "semester"])])),
        ("regression", Ridge(alpha=1.0, random_state=SEED))])


def evaluate(actual, predicted):
    return {"mae": float(mean_absolute_error(actual, predicted)),
            "rmse": float(root_mean_squared_error(actual, predicted))}
