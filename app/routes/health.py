"""Health and model-info endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.responses import HealthResponse, ModelInfoResponse
from app.services.model_service import ModelService
from app.services.registry import get_model_service

router = APIRouter(prefix="/api", tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health(model: ModelService = Depends(get_model_service)) -> HealthResponse:
    return HealthResponse(status="ok", model_loaded=model.is_ready)


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info(model: ModelService = Depends(get_model_service)) -> ModelInfoResponse:
    if not model.is_ready:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    return ModelInfoResponse(**model.model_info())
