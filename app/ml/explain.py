"""Per-prediction explanations derived from the actual trained model.

Two honest, model-based strategies are implemented:

* Linear models (logistic regression): the signed contribution of each feature
  is ``coefficient * standardized_value``, aggregated back to the original
  columns. This is the model's genuine linear decomposition of the log-odds.

* Other models (random forest): a "what-if" / occlusion method. For each
  feature we substitute a neutral baseline value and measure how the predicted
  churn probability changes. A drop in probability when a feature is neutralized
  means that feature was pushing the prediction toward churn.

Both describe *model feature importance for this input*, not causation. The API
and UI label them accordingly and never claim a feature "caused" churn.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from app.ml.features import FEATURE_ORDER, describe_feature_value


@dataclass
class Factor:
    feature: str
    value: object
    description: str
    direction: str  # "increases" or "decreases" churn risk
    weight: float  # normalized magnitude in [0, 1]

    def as_dict(self) -> dict:
        return {
            "feature": self.feature,
            "value": self.value,
            "description": self.description,
            "direction": self.direction,
            "weight": round(self.weight, 4),
        }


def _map_transformed_to_original(names: list[str]) -> list[str]:
    """Map ColumnTransformer output names back to original feature names."""
    originals = []
    for name in names:
        _, _, rest = name.partition("__")  # strip 'num__' / 'cat__' / 'bin__'
        matched = None
        for feat in FEATURE_ORDER:
            if rest == feat or rest.startswith(feat + "_"):
                matched = feat
                break
        originals.append(matched or rest)
    return originals


def _contributions_linear(pipeline, row: pd.DataFrame) -> dict[str, float]:
    pre = pipeline.named_steps["preprocess"]
    clf: LogisticRegression = pipeline.named_steps["classifier"]

    transformed = pre.transform(row)
    if hasattr(transformed, "toarray"):
        transformed = transformed.toarray()
    coefs = clf.coef_[0]
    per_column = transformed[0] * coefs

    names = list(pre.get_feature_names_out())
    originals = _map_transformed_to_original(names)

    contributions: dict[str, float] = {}
    for feat, contrib in zip(originals, per_column):
        contributions[feat] = contributions.get(feat, 0.0) + float(contrib)
    return contributions


def _contributions_occlusion(
    pipeline, row: pd.DataFrame, baselines: dict[str, object]
) -> dict[str, float]:
    base_prob = float(pipeline.predict_proba(row)[0, 1])
    contributions: dict[str, float] = {}
    for feat in FEATURE_ORDER:
        if feat not in baselines:
            continue
        modified = row.copy()
        modified.at[modified.index[0], feat] = baselines[feat]
        new_prob = float(pipeline.predict_proba(modified)[0, 1])
        # Positive => neutralizing the feature lowered churn prob, so the real
        # value was pushing the prediction toward churn.
        contributions[feat] = base_prob - new_prob
    return contributions


def explain_prediction(
    pipeline,
    row: pd.DataFrame,
    baselines: dict[str, object],
    top_n: int = 4,
) -> list[dict]:
    """Return the top contributing factors for a single-row prediction."""
    clf = pipeline.named_steps["classifier"]
    if isinstance(clf, LogisticRegression):
        contributions = _contributions_linear(pipeline, row)
    else:
        contributions = _contributions_occlusion(pipeline, row, baselines)

    if not contributions:
        return []

    max_magnitude = max(abs(v) for v in contributions.values()) or 1.0
    ranked = sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)

    factors: list[Factor] = []
    for feat, contrib in ranked[:top_n]:
        value = row.iloc[0][feat]
        if isinstance(value, (np.generic,)):
            value = value.item()
        factors.append(
            Factor(
                feature=feat,
                value=value,
                description=describe_feature_value(feat, value),
                direction="increases" if contrib >= 0 else "decreases",
                weight=abs(contrib) / max_magnitude,
            )
        )
    return [f.as_dict() for f in factors]
