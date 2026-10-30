"""Explicit configuration for the SQL -> MLflow -> draft proposal journey."""
import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit
from sqlalchemy import create_engine
from src.common.settings import required


@dataclass
class Settings:
    source: str = field(repr=False)
    application: str = field(repr=False)
    tracking: str
    ui: str
    experiment: str
    model_name: str
    api: str
    inference: str
    cycle: str = "2026-1"
    course: str | None = None
    timeout: int = 15
    retries: int = 2
    mode: str = "DEMO"

    @classmethod
    def load(cls):
        cfg = cls(required("SOURCE_DATABASE_URL"), required("APPLICATION_DATABASE_URL"),
            required("MLFLOW_TRACKING_URI"), required("MLFLOW_UI_BASE_URL"),
            required("MLFLOW_EXPERIMENT_NAME"), required("MODEL_NAME"),
            required("API_URI"), required("INFERENCE_URI"),
            os.getenv("JOURNEY_CYCLE", "2026-1"), os.getenv("JOURNEY_COURSE") or None,
            int(os.getenv("JOURNEY_TIMEOUT", "15")), int(os.getenv("JOURNEY_RETRIES", "2")),
            os.getenv("JOURNEY_MODE", "DEMO"))
        if cfg.mode != "DEMO":
            raise ValueError("Only explicit DEMO is configured. REAL requires a validated source contract; no fallback.")
        for name in ("tracking", "ui", "api", "inference"):
            uri = urlsplit(getattr(cfg, name))
            if uri.scheme not in ("http", "https") or not uri.netloc or uri.username or uri.password:
                raise ValueError(f"{name}: remote HTTP(S) endpoint without credentials required")
        if not 1 <= cfg.timeout <= 60 or not 0 <= cfg.retries <= 3:
            raise ValueError("Timeout must be 1..60s and retries 0..3")
        for name in ("source", "application"):
            if not getattr(cfg, name).startswith("postgresql"):
                raise ValueError(f"{name}: PostgreSQL required")
        return cfg


def sql_engine(url, timeout=15):
    return create_engine(url, pool_pre_ping=True, hide_parameters=True,
        connect_args={"connect_timeout": timeout, "options": f"-c statement_timeout={timeout * 1000}"})
