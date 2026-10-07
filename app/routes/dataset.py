"""Dataset statistics endpoint for the dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.services.dataset_service import DatasetService
from app.services.registry import get_dataset_service
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/dataset", tags=["dataset"])


@router.get("/stats")
def dataset_stats(
    dataset: DatasetService = Depends(get_dataset_service),
) -> dict:
    try:
        return dataset.stats()
    except FileNotFoundError:
        raise HTTPException(status_code=503, detail="Dataset is unavailable")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to compute dataset statistics: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to compute statistics: {exc}")
