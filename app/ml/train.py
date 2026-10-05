"""Reproducible training pipeline.

Run via the ``backend/train.py`` entry point. Produces, in ``MODEL_DIR``:

* ``churn_pipeline.joblib``   -- the selected end-to-end sklearn pipeline
* ``metrics.json``            -- evaluation metrics for every candidate model
* ``feature_metadata.json``   -- feature schema + baselines for explanations
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.config import get_settings
from app.ml.data import load_clean, split_features_target
from app.ml.features import (
    BINARY_NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    FEATURE_ORDER,
    NUMERIC_FEATURES,
)
from app.ml.preprocessing import build_preprocessor
from app.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)

RANDOM_STATE = 42
MODEL_VERSION = "1.0.0"

# Metric used to choose the production model. ROC-AUC is threshold-independent
# and appropriate for the class imbalance present in churn data.
SELECTION_METRIC = "roc_auc"


def _build_candidates() -> dict[str, Pipeline]:
    """Return the candidate model pipelines.

    ``class_weight="balanced"`` is used on both models to counter the ~73/27
    class imbalance without resampling the data.
    """
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=1000,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("preprocess", build_preprocessor()),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=200,
                        max_depth=12,
                        min_samples_leaf=5,
                        class_weight="balanced",
                        random_state=RANDOM_STATE,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def _evaluate(pipeline: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    return {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }


def _compute_baselines(X: pd.DataFrame) -> dict[str, object]:
    """Neutral baseline value per feature, used by the occlusion explainer."""
    baselines: dict[str, object] = {}
    for feat in NUMERIC_FEATURES:
        baselines[feat] = round(float(X[feat].median()), 2)
    for feat in BINARY_NUMERIC_FEATURES:
        baselines[feat] = int(X[feat].mode().iloc[0])
    for feat in CATEGORICAL_FEATURES:
        baselines[feat] = str(X[feat].mode().iloc[0])
    return baselines


def train(data_path: str | Path | None = None, model_dir: str | Path | None = None) -> dict:
    """Train, evaluate, select, and persist the churn model.

    Returns the full results dict (also written to ``metrics.json``).
    """
    settings = get_settings()
    data_path = Path(data_path or settings.data_path)
    model_dir = Path(model_dir or settings.model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Loading dataset from %s", data_path)
    df = load_clean(data_path)
    X, y = split_features_target(df)
    X = X[FEATURE_ORDER]  # enforce column order

    logger.info("Dataset: %d rows, churn rate %.1f%%", len(y), 100 * y.mean())

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    results: dict[str, dict] = {}
    fitted: dict[str, Pipeline] = {}
    for name, pipeline in _build_candidates().items():
        logger.info("Training %s ...", name)
        pipeline.fit(X_train, y_train)
        metrics = _evaluate(pipeline, X_test, y_test)
        results[name] = metrics
        fitted[name] = pipeline
        logger.info(
            "%s -> acc=%.3f f1=%.3f roc_auc=%.3f",
            name,
            metrics["accuracy"],
            metrics["f1"],
            metrics["roc_auc"],
        )

    best_name = max(results, key=lambda n: results[n][SELECTION_METRIC])
    best_pipeline = fitted[best_name]
    logger.info("Selected '%s' by %s", best_name, SELECTION_METRIC)

    # Refit the winner on the full dataset so the shipped model uses all data.
    best_pipeline.fit(X, y)

    # Persist artifacts. compress=3 keeps the file small enough for a
    # serverless deployment bundle without a meaningful load-time penalty.
    joblib.dump(best_pipeline, model_dir / "churn_pipeline.joblib", compress=3)

    summary = {
        "selected_model": best_name,
        "selection_metric": SELECTION_METRIC,
        "model_version": MODEL_VERSION,
        "trained_on": date.today().isoformat(),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "total_rows": int(len(X)),
        "churn_rate": round(float(y.mean()), 4),
        "models": results,
    }
    (model_dir / "metrics.json").write_text(json.dumps(summary, indent=2))

    metadata = {
        "model_version": MODEL_VERSION,
        "feature_order": FEATURE_ORDER,
        "numeric_features": NUMERIC_FEATURES,
        "binary_numeric_features": BINARY_NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "baselines": _compute_baselines(X),
        "feature_count": len(FEATURE_ORDER),
    }
    (model_dir / "feature_metadata.json").write_text(json.dumps(metadata, indent=2))

    logger.info("Artifacts written to %s", model_dir)
    return summary


def main() -> None:
    configure_logging(get_settings().log_level)
    summary = train()
    best = summary["selected_model"]
    m = summary["models"][best]
    print("\n=== Training complete ===")
    print(f"Selected model : {best}")
    print(f"Accuracy       : {m['accuracy']}")
    print(f"Precision      : {m['precision']}")
    print(f"Recall         : {m['recall']}")
    print(f"F1             : {m['f1']}")
    print(f"ROC-AUC        : {m['roc_auc']}")


if __name__ == "__main__":
    main()
