"""Model service: loads the serialized pipeline and serves predictions.

A single instance is created at startup. If the model artifacts are missing the
service loads in a degraded state (``is_ready`` is False) rather than crashing,
so the health endpoint can report the problem cleanly.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from app.config import Settings
from app.ml.explain import explain_prediction
from app.ml.features import FEATURE_ORDER
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Probability thresholds for mapping to a risk band.
RISK_THRESHOLDS = {"medium": 0.40, "high": 0.65}


class ModelNotLoadedError(RuntimeError):
    """Raised when a prediction is attempted without a loaded model."""


class ModelService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pipeline = None
        self._metrics: dict = {}
        self._metadata: dict = {}

    def load(self) -> None:
        """Load model artifacts from disk. Safe to call once at startup."""
        model_path = self._settings.model_path
        if not model_path.exists():
            logger.error(
                "Model file not found at %s. Run 'python train.py' first.", model_path
            )
            return
        try:
            self._pipeline = joblib.load(model_path)
            self._metrics = self._read_json(self._settings.metrics_path)
            self._metadata = self._read_json(self._settings.metadata_path)
            logger.info("Model loaded from %s", model_path)
        except Exception:  # noqa: BLE001 - log and stay degraded
            logger.exception("Failed to load model artifacts")
            self._pipeline = None

    @staticmethod
    def _read_json(path: Path) -> dict:
        if path.exists():
            return json.loads(path.read_text())
        return {}

    @property
    def is_ready(self) -> bool:
        return self._pipeline is not None

    @property
    def baselines(self) -> dict:
        return self._metadata.get("baselines", {})

    def model_info(self) -> dict:
        selected = self._metrics.get("selected_model", "unknown")
        return {
            "model_name": selected,
            "model_version": self._metrics.get("model_version", "unknown"),
            "trained_on": self._metrics.get("trained_on"),
            "selection_metric": self._metrics.get("selection_metric", "roc_auc"),
            "feature_count": self._metadata.get("feature_count", len(FEATURE_ORDER)),
            "metrics": self._metrics.get("models", {}).get(selected, {}),
            "all_models": self._metrics.get("models", {}),
            "dataset": {
                "total_rows": self._metrics.get("total_rows"),
                "train_rows": self._metrics.get("train_rows"),
                "test_rows": self._metrics.get("test_rows"),
                "churn_rate": self._metrics.get("churn_rate"),
            },
        }

    @property
    def full_metrics(self) -> dict:
        return self._metrics

    @staticmethod
    def _risk_level(prob: float) -> str:
        if prob >= RISK_THRESHOLDS["high"]:
            return "high"
        if prob >= RISK_THRESHOLDS["medium"]:
            return "medium"
        return "low"

    @staticmethod
    def _build_explanation(prediction: str, risk: str, factors: list[dict]) -> str:
        drivers = [f["description"] for f in factors if f["direction"] == "increases"][:3]
        verb = "likely to churn" if prediction == "churn" else "likely to stay"
        if drivers:
            joined = "; ".join(drivers)
            return (
                f"The model estimates this customer is {verb} ({risk} risk). "
                f"The factors most associated with this prediction are: {joined}. "
                "These reflect patterns the model learned, not proven causes."
            )
        return f"The model estimates this customer is {verb} ({risk} risk)."

    def predict_one(self, features: dict) -> dict:
        """Predict churn for a single customer feature dict."""
        if not self.is_ready:
            raise ModelNotLoadedError("Model is not loaded")

        row = pd.DataFrame([features])[FEATURE_ORDER]
        prob = float(self._pipeline.predict_proba(row)[0, 1])
        prediction = "churn" if prob >= 0.5 else "no_churn"
        risk = self._risk_level(prob)
        factors = explain_prediction(self._pipeline, row, self.baselines)
        explanation = self._build_explanation(prediction, risk, factors)

        return {
            "prediction": prediction,
            "churn_probability": round(prob, 4),
            "risk_level": risk,
            "top_factors": factors,
            "explanation": explanation,
        }

    def predict_many(self, customers: list[dict]) -> list[dict]:
        return [self.predict_one(c) for c in customers]
