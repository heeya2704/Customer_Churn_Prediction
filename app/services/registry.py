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

# Load the model at import time. This is important for serverless platforms
# (e.g. Vercel) whose ASGI runtime may not trigger FastAPI's lifespan startup.
# load() is idempotent and never raises, so importing stays safe even if the
# model file is missing (the health endpoint then reports model_loaded=false).
model_service.load()


def init_services() -> None:
    """(Re)load model artifacts. Called from the app lifespan for local runs."""
    model_service.load()


def get_model_service() -> ModelService:
    return model_service


def get_dataset_service() -> DatasetService:
    return dataset_service
