"""Dataset statistics service.

Computes aggregate figures for the dashboard from the cleaned dataset. All
numbers are derived from the real data (and, for the probability distribution,
from the real model) -- nothing is hardcoded. Results are cached after first
computation because the dataset is static at runtime.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.config import Settings
from app.ml.data import load_clean
from app.ml.features import FEATURE_ORDER, TARGET
from app.services.model_service import ModelService
from app.utils.logging import get_logger

logger = get_logger(__name__)


class DatasetService:
    def __init__(self, settings: Settings, model_service: ModelService) -> None:
        self._settings = settings
        self._model_service = model_service
        self._cache: dict | None = None
        self._df: pd.DataFrame | None = None

    def _ensure_loaded(self) -> pd.DataFrame:
        if self._df is None:
            self._df = load_clean(self._settings.data_path)
            self._df["_churn"] = (
                self._df[TARGET].astype(str).str.strip().str.lower() == "yes"
            ).astype(int)
        return self._df

    @staticmethod
    def _group_churn(df: pd.DataFrame, column: str) -> list[dict]:
        grouped = df.groupby(column)["_churn"].agg(["count", "sum"]).reset_index()
        rows = []
        for _, r in grouped.iterrows():
            total = int(r["count"])
            churned = int(r["sum"])
            rows.append(
                {
                    "category": str(r[column]),
                    "total": total,
                    "churned": churned,
                    "churn_rate": round(churned / total, 4) if total else 0.0,
                }
            )
        return rows

    @staticmethod
    def _tenure_buckets(df: pd.DataFrame) -> list[dict]:
        bins = [0, 12, 24, 48, 60, np.inf]
        labels = ["0-12", "13-24", "25-48", "49-60", "60+"]
        cat = pd.cut(df["tenure"], bins=bins, labels=labels, include_lowest=True)
        tmp = df.assign(_bucket=cat)
        rows = []
        for label in labels:
            sub = tmp[tmp["_bucket"] == label]
            total = len(sub)
            churned = int(sub["_churn"].sum())
            rows.append(
                {
                    "category": label,
                    "total": total,
                    "churned": churned,
                    "churn_rate": round(churned / total, 4) if total else 0.0,
                }
            )
        return rows

    @staticmethod
    def _charges_distribution(df: pd.DataFrame) -> list[dict]:
        bins = list(range(0, 121, 20))
        cat = pd.cut(df["MonthlyCharges"], bins=bins, include_lowest=True)
        tmp = df.assign(_bin=cat)
        rows = []
        for interval, sub in tmp.groupby("_bin", observed=True):
            rows.append(
                {
                    "range": f"${int(interval.left)}-${int(interval.right)}",
                    "churned": int(sub["_churn"].sum()),
                    "retained": int((sub["_churn"] == 0).sum()),
                }
            )
        return rows

    def _probability_distribution(self, df: pd.DataFrame) -> list[dict]:
        if not self._model_service.is_ready:
            return []
        X = df[FEATURE_ORDER]
        probs = self._model_service._pipeline.predict_proba(X)[:, 1]
        bins = np.linspace(0, 1, 11)
        counts, edges = np.histogram(probs, bins=bins)
        return [
            {
                "range": f"{int(edges[i] * 100)}-{int(edges[i + 1] * 100)}%",
                "count": int(counts[i]),
            }
            for i in range(len(counts))
        ]

    def stats(self) -> dict:
        if self._cache is not None:
            return self._cache

        df = self._ensure_loaded()
        total = len(df)
        churned = int(df["_churn"].sum())

        self._cache = {
            "total_customers": total,
            "churned": churned,
            "retained": total - churned,
            "churn_rate": round(churned / total, 4),
            "retention_rate": round((total - churned) / total, 4),
            "avg_monthly_charges": round(float(df["MonthlyCharges"].mean()), 2),
            "avg_tenure": round(float(df["tenure"].mean()), 1),
            "churn_by_contract": self._group_churn(df, "Contract"),
            "churn_by_payment_method": self._group_churn(df, "PaymentMethod"),
            "churn_by_internet_service": self._group_churn(df, "InternetService"),
            "churn_by_tenure": self._tenure_buckets(df),
            "monthly_charges_distribution": self._charges_distribution(df),
            "churn_probability_distribution": self._probability_distribution(df),
        }
        logger.info("Dataset statistics computed for %d customers", total)
        return self._cache
