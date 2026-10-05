"""Prediction endpoints (single and batch)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.customer import BatchPredictRequest, CustomerFeatures
from app.schemas.responses import BatchPredictionResponse, PredictionResponse
from app.services.model_service import ModelNotLoadedError, ModelService
from app.services.registry import get_model_service
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["prediction"])


@router.post("/predict", response_model=PredictionResponse)
def predict(
    customer: CustomerFeatures,
    model: ModelService = Depends(get_model_service),
) -> PredictionResponse:
    try:
        result = model.predict_one(customer.to_feature_dict())
    except ModelNotLoadedError:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    except Exception:  # noqa: BLE001
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Prediction failed")
    return PredictionResponse(**result)


@router.post("/predict/batch", response_model=BatchPredictionResponse)
def predict_batch(
    request: BatchPredictRequest,
    model: ModelService = Depends(get_model_service),
) -> BatchPredictionResponse:
    try:
        results = model.predict_many([c.to_feature_dict() for c in request.customers])
    except ModelNotLoadedError:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    except Exception:  # noqa: BLE001
        logger.exception("Batch prediction failed")
        raise HTTPException(status_code=500, detail="Batch prediction failed")
    return BatchPredictionResponse(
        count=len(results),
        predictions=[PredictionResponse(**r) for r in results],
    )
