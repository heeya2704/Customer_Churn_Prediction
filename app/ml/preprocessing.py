"""Preprocessing pipeline shared by training and inference.

A single ``ColumnTransformer`` is fitted during training and serialized as part
of the model pipeline, guaranteeing that prediction-time preprocessing is byte
-for-byte identical to training-time preprocessing.
"""

from __future__ import annotations

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.features import (
    BINARY_NUMERIC_FEATURES,
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)


def build_preprocessor() -> ColumnTransformer:
    """Build the feature preprocessing transformer.

    - Numeric features: median imputation (robust to outliers) + standard scaling.
      Scaling matters for logistic regression and is harmless for tree models.
    - Binary numeric (SeniorCitizen): passed through as-is; already 0/1.
    - Categorical features: most-frequent imputation + one-hot encoding with
      ``handle_unknown="ignore"`` so unseen categories do not crash inference.
    """
    numeric_pipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("bin", "passthrough", BINARY_NUMERIC_FEATURES),
            ("cat", categorical_pipeline, list(CATEGORICAL_FEATURES.keys())),
        ],
        remainder="drop",
    )
