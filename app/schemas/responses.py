"""Response schemas returned by the API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Factor(BaseModel):
    feature: str
    value: object
    description: str
    direction: Literal["increases", "decreases"]
    weight: float


class PredictionResponse(BaseModel):
    prediction: Literal["churn", "no_churn"]
    churn_probability: float
    risk_level: Literal["low", "medium", "high"]
    top_factors: list[Factor]
    explanation: str


class BatchPredictionResponse(BaseModel):
    count: int
    predictions: list[PredictionResponse]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


class ModelInfoResponse(BaseModel):
    # Allow "model_*" field names (they describe the ML model, not Pydantic).
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    model_version: str
    trained_on: str | None
    selection_metric: str
    feature_count: int
    metrics: dict
    all_models: dict  # per-candidate metrics, for the comparison view
    dataset: dict  # row counts / churn rate used in training


class ErrorResponse(BaseModel):
    detail: str
