"""Request schemas for customer input, validated against the model's schema."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.ml.features import CATEGORICAL_FEATURES, NUMERIC_BOUNDS

# Build Literal types from the single source of truth so validation can never
# drift from what the model was trained on.
Gender = Literal["Female", "Male"]
YesNo = Literal["Yes", "No"]
MultipleLines = Literal["Yes", "No", "No phone service"]
InternetService = Literal["DSL", "Fiber optic", "No"]
InternetAddon = Literal["Yes", "No", "No internet service"]
Contract = Literal["Month-to-month", "One year", "Two year"]
PaymentMethod = Literal[
    "Electronic check",
    "Mailed check",
    "Bank transfer (automatic)",
    "Credit card (automatic)",
]


class CustomerFeatures(BaseModel):
    """A single customer's attributes.

    Field names match the dataset columns exactly so the payload maps directly
    onto the model's expected feature set.
    """

    gender: Gender
    SeniorCitizen: int = Field(..., ge=0, le=1, description="0 = no, 1 = yes")
    Partner: YesNo
    Dependents: YesNo
    tenure: int = Field(..., ge=NUMERIC_BOUNDS["tenure"][0], le=NUMERIC_BOUNDS["tenure"][1])
    PhoneService: YesNo
    MultipleLines: MultipleLines
    InternetService: InternetService
    OnlineSecurity: InternetAddon
    OnlineBackup: InternetAddon
    DeviceProtection: InternetAddon
    TechSupport: InternetAddon
    StreamingTV: InternetAddon
    StreamingMovies: InternetAddon
    Contract: Contract
    PaperlessBilling: YesNo
    PaymentMethod: PaymentMethod
    MonthlyCharges: float = Field(
        ..., ge=NUMERIC_BOUNDS["MonthlyCharges"][0], le=NUMERIC_BOUNDS["MonthlyCharges"][1]
    )
    TotalCharges: float = Field(
        ..., ge=NUMERIC_BOUNDS["TotalCharges"][0], le=NUMERIC_BOUNDS["TotalCharges"][1]
    )

    def to_feature_dict(self) -> dict:
        """Return a plain dict suitable for building a model input row."""
        return self.model_dump()

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "gender": "Female",
                "SeniorCitizen": 0,
                "Partner": "No",
                "Dependents": "No",
                "tenure": 2,
                "PhoneService": "Yes",
                "MultipleLines": "No",
                "InternetService": "Fiber optic",
                "OnlineSecurity": "No",
                "OnlineBackup": "No",
                "DeviceProtection": "No",
                "TechSupport": "No",
                "StreamingTV": "Yes",
                "StreamingMovies": "Yes",
                "Contract": "Month-to-month",
                "PaperlessBilling": "Yes",
                "PaymentMethod": "Electronic check",
                "MonthlyCharges": 95.0,
                "TotalCharges": 190.0,
            }
        },
    }


class BatchPredictRequest(BaseModel):
    model_config = {"extra": "forbid"}
    customers: list[CustomerFeatures] = Field(..., min_length=1, max_length=1000)


# Sanity guard: ensure the Literal choices cover the dataset's categories.
assert set(CATEGORICAL_FEATURES["PaymentMethod"]) == set(PaymentMethod.__args__)
