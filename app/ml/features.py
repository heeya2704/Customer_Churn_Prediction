"""Single source of truth for the model's feature schema.

Both the training pipeline and the inference layer import these definitions so
that the columns, their order, and their allowed values can never drift apart.
"""

from __future__ import annotations

# Target column in the raw dataset.
TARGET = "Churn"

# Column we drop before training -- it is an identifier, not a feature.
ID_COLUMN = "customerID"

# Numeric features fed to the model.
NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]

# SeniorCitizen is stored as 0/1 in the raw data. We keep it numeric so the
# model treats it as a simple binary indicator.
BINARY_NUMERIC_FEATURES = ["SeniorCitizen"]

# Categorical features and the exact set of values the model was trained on.
# Unknown categories at inference time are ignored by the one-hot encoder
# (handle_unknown="ignore"), but we still validate against these at the API
# boundary to give callers a clear error.
CATEGORICAL_FEATURES: dict[str, list[str]] = {
    "gender": ["Female", "Male"],
    "Partner": ["Yes", "No"],
    "Dependents": ["Yes", "No"],
    "PhoneService": ["Yes", "No"],
    "MultipleLines": ["Yes", "No", "No phone service"],
    "InternetService": ["DSL", "Fiber optic", "No"],
    "OnlineSecurity": ["Yes", "No", "No internet service"],
    "OnlineBackup": ["Yes", "No", "No internet service"],
    "DeviceProtection": ["Yes", "No", "No internet service"],
    "TechSupport": ["Yes", "No", "No internet service"],
    "StreamingTV": ["Yes", "No", "No internet service"],
    "StreamingMovies": ["Yes", "No", "No internet service"],
    "Contract": ["Month-to-month", "One year", "Two year"],
    "PaperlessBilling": ["Yes", "No"],
    "PaymentMethod": [
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)",
    ],
}

# Full ordered list of model input columns.
FEATURE_ORDER: list[str] = (
    BINARY_NUMERIC_FEATURES
    + NUMERIC_FEATURES
    + list(CATEGORICAL_FEATURES.keys())
)

# Reasonable physical bounds used for validation. These are deliberately a bit
# wider than the training data so we accept plausible new customers without
# rejecting them, while still catching nonsense input.
NUMERIC_BOUNDS: dict[str, tuple[float, float]] = {
    "tenure": (0, 120),
    "MonthlyCharges": (0, 1000),
    "TotalCharges": (0, 100000),
}

# Human-readable labels used in explanations and the frontend.
FEATURE_LABELS: dict[str, str] = {
    "tenure": "Customer tenure (months)",
    "MonthlyCharges": "Monthly charges",
    "TotalCharges": "Total charges",
    "SeniorCitizen": "Senior citizen",
    "gender": "Gender",
    "Partner": "Has partner",
    "Dependents": "Has dependents",
    "PhoneService": "Phone service",
    "MultipleLines": "Multiple lines",
    "InternetService": "Internet service",
    "OnlineSecurity": "Online security",
    "OnlineBackup": "Online backup",
    "DeviceProtection": "Device protection",
    "TechSupport": "Tech support",
    "StreamingTV": "Streaming TV",
    "StreamingMovies": "Streaming movies",
    "Contract": "Contract type",
    "PaperlessBilling": "Paperless billing",
    "PaymentMethod": "Payment method",
}


def describe_feature_value(feature: str, value: object) -> str:
    """Return a short human phrase describing a feature/value pair.

    Used to turn a model-driven factor into readable text such as
    "Month-to-month contract" or "Short tenure (3 months)".
    """
    label = FEATURE_LABELS.get(feature, feature)
    if feature == "Contract":
        return f"{value} contract"
    if feature == "tenure":
        return f"{label}: {value} months"
    if feature in ("MonthlyCharges", "TotalCharges"):
        return f"{label}: {value}"
    if feature == "SeniorCitizen":
        return "Senior citizen" if value in (1, "1", True) else "Not a senior citizen"
    return f"{label}: {value}"
