"""Exploratory data analysis for the Telco churn dataset.

Run from the repository root:  ``python training/eda.py``

Prints a text summary (shape, missing values, dtypes, target balance, churn
relationships) and saves figures to ``reports/figures/``. All observations are
computed from the data -- nothing is hardcoded.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend; safe on servers / CI
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ml.data import load_clean  # noqa: E402
from app.ml.features import NUMERIC_FEATURES, TARGET  # noqa: E402

FIG_DIR = ROOT / "reports" / "figures"


def _target_bool(df: pd.DataFrame) -> pd.Series:
    return (df[TARGET].astype(str).str.strip().str.lower() == "yes").astype(int)


def summarize(df: pd.DataFrame) -> None:
    print("=" * 60)
    print("DATASET OVERVIEW")
    print("=" * 60)
    print(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns\n")

    print("Missing values per column:")
    missing = df.isna().sum()
    print(missing[missing > 0].to_string() if missing.any() else "  none")
    print()

    print("Data types:")
    print(df.dtypes.to_string())
    print()

    y = _target_bool(df)
    print("Target distribution (Churn):")
    counts = df[TARGET].value_counts()
    for label, count in counts.items():
        print(f"  {label}: {count} ({count / len(df):.1%})")
    print()

    print("Numeric feature summary:")
    print(df[NUMERIC_FEATURES].describe().round(2).to_string())
    print()

    print("Churn rate by key categorical feature:")
    for col in ["Contract", "InternetService", "PaymentMethod"]:
        print(f"\n  {col}:")
        rate = df.assign(_c=y).groupby(col)["_c"].mean().sort_values(ascending=False)
        for cat, r in rate.items():
            print(f"    {cat:<28} {r:.1%}")
    print()


def make_figures(df: pd.DataFrame) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    y = _target_bool(df)

    # 1. Target balance
    fig, ax = plt.subplots(figsize=(5, 4))
    df[TARGET].value_counts().plot(kind="bar", color=["#10b981", "#ef4444"], ax=ax)
    ax.set_title("Churn distribution")
    ax.set_ylabel("Customers")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "target_distribution.png", dpi=120)
    plt.close(fig)

    # 2. Churn rate by contract
    fig, ax = plt.subplots(figsize=(6, 4))
    (df.assign(_c=y).groupby("Contract")["_c"].mean() * 100).plot(
        kind="bar", color="#2563eb", ax=ax
    )
    ax.set_title("Churn rate by contract")
    ax.set_ylabel("Churn rate (%)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "churn_by_contract.png", dpi=120)
    plt.close(fig)

    # 3. Tenure distribution by churn
    fig, ax = plt.subplots(figsize=(6, 4))
    for label, color in [(0, "#10b981"), (1, "#ef4444")]:
        sns.kdeplot(df.loc[y == label, "tenure"], fill=True, alpha=0.4, color=color,
                    label="Churn" if label else "Retained", ax=ax)
    ax.set_title("Tenure by churn status")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "tenure_by_churn.png", dpi=120)
    plt.close(fig)

    # 4. Correlation heatmap (numeric)
    fig, ax = plt.subplots(figsize=(5, 4))
    corr = df[NUMERIC_FEATURES].assign(Churn=y).corr()
    sns.heatmap(corr, annot=True, cmap="Blues", fmt=".2f", ax=ax)
    ax.set_title("Numeric correlations")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "correlation_heatmap.png", dpi=120)
    plt.close(fig)

    print(f"Saved 4 figures to {FIG_DIR}")


def main() -> None:
    from app.config import get_settings

    df = load_clean(get_settings().data_path)
    summarize(df)
    make_figures(df)


if __name__ == "__main__":
    main()
