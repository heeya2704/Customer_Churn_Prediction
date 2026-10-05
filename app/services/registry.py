"""Service singletons wired up at application startup.

Kept in one place so routes can depend on ready-to-use instances without each
route re-loading the model or dataset.
"""

from __future__ import annotations

from app.config import get_settings
from app.services.dataset_service import DatasetService
from app.services.model_service import ModelService

_settings = get_settings()
model_service = ModelService(_settings)
dataset_service = DatasetService(_settings, model_service)


def init_services() -> None:
    """Load model artifacts. Called once during app startup."""
    model_service.load()


def get_model_service() -> ModelService:
    return model_service


def get_dataset_service() -> DatasetService:
    return dataset_service
