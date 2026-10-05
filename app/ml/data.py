"""Dataset loading and cleaning.

Kept separate from the training script so the same cleaning logic can be reused
by the dataset-statistics service without duplicating code.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.ml.features import ID_COLUMN, TARGET


def load_raw(csv_path: str | Path) -> pd.DataFrame:
    """Load the raw CSV exactly as shipped."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset not found at {csv_path}")
    return pd.read_csv(csv_path)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the raw Telco dataframe.

    - ``TotalCharges`` ships as text with blank strings for brand-new customers
      (tenure == 0). We coerce it to numeric and fill those blanks with 0, which
      is the economically correct value for a customer who has not been billed.
    - Drop the identifier column; it carries no predictive signal.
    """
    df = df.copy()

    if "TotalCharges" in df.columns:
        df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
        # Blanks correspond to tenure == 0, so total charges are genuinely 0.
        df["TotalCharges"] = df["TotalCharges"].fillna(0.0)

    if ID_COLUMN in df.columns:
        df = df.drop(columns=[ID_COLUMN])

    return df


def load_clean(csv_path: str | Path) -> pd.DataFrame:
    """Convenience wrapper: load then clean."""
    return clean(load_raw(csv_path))


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Split a cleaned dataframe into X and a binary 0/1 target."""
    if TARGET not in df.columns:
        raise ValueError(f"Target column '{TARGET}' missing from dataframe")
    y = (df[TARGET].astype(str).str.strip().str.lower() == "yes").astype(int)
    X = df.drop(columns=[TARGET])
    return X, y
