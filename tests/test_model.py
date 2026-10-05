"""ML smoke tests: the production model loads and makes real predictions."""

from __future__ import annotations

import pandas as pd

from app.config import get_settings
from app.ml.features import FEATURE_ORDER
from app.services.model_service import ModelService


def test_model_file_exists():
    settings = get_settings()
    assert settings.model_path.exists(), "Run 'python train.py' to create the model"


def test_model_loads_and_is_ready():
    service = ModelService(get_settings())
    service.load()
    assert service.is_ready


def test_prediction_probability_in_range(valid_customer):
    service = ModelService(get_settings())
    service.load()
    result = service.predict_one(valid_customer)
    assert 0.0 <= result["churn_probability"] <= 1.0


def test_pipeline_transforms_sample(valid_customer):
    service = ModelService(get_settings())
    service.load()
    row = pd.DataFrame([valid_customer])[FEATURE_ORDER]
    transformed = service._pipeline.named_steps["preprocess"].transform(row)
    assert transformed.shape[0] == 1
    assert transformed.shape[1] > len(FEATURE_ORDER)  # one-hot expands columns


def test_feature_metadata_matches_schema():
    service = ModelService(get_settings())
    service.load()
    meta_order = service._metadata["feature_order"]
    assert meta_order == FEATURE_ORDER
    assert service._metadata["feature_count"] == len(FEATURE_ORDER)


def test_explanation_factors_present(valid_customer):
    service = ModelService(get_settings())
    service.load()
    result = service.predict_one(valid_customer)
    assert len(result["top_factors"]) >= 1
    for factor in result["top_factors"]:
        assert factor["direction"] in ("increases", "decreases")
        assert 0.0 <= factor["weight"] <= 1.0
