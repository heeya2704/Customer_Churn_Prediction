"""Application configuration loaded from environment variables.

All paths are resolved relative to the backend package so the app never depends
on an absolute or OS-specific location.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

# app/config.py -> repository root (parent of the ``app`` package).
BASE_DIR = Path(__file__).resolve().parent.parent

# Load a local .env file if python-dotenv is available. It is a dev convenience;
# production platforms inject real environment variables.
try:  # pragma: no cover - trivial import guard
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:  # pragma: no cover
    pass


class Settings:
    """Runtime settings. Instantiate via :func:`get_settings`."""

    def __init__(self) -> None:
        self.app_name: str = os.getenv("APP_NAME", "Churn Prediction API")
        self.environment: str = os.getenv("ENVIRONMENT", "development")
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

        self.model_dir: Path = Path(
            os.getenv("MODEL_DIR", str(BASE_DIR / "model"))
        )
        self.model_path: Path = self.model_dir / "churn_pipeline.joblib"
        self.metrics_path: Path = self.model_dir / "metrics.json"
        self.metadata_path: Path = self.model_dir / "feature_metadata.json"

        self.data_path: Path = Path(
            os.getenv("DATA_PATH", str(BASE_DIR / "data" / "telco_churn.csv"))
        )

        # Comma-separated list of allowed CORS origins.
        raw_origins = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
            "https://customer-churn-prediction-3zjl.vercel.app",
        )
        self.cors_origins: list[str] = [
            o.strip() for o in raw_origins.split(",") if o.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
