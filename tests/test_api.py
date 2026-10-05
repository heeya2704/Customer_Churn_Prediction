"""API endpoint tests covering happy paths and validation/error handling."""

from __future__ import annotations

import copy

import pytest


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["model_loaded"] is True


def test_model_info(client):
    resp = client.get("/api/model-info")
    assert resp.status_code == 200
    body = resp.json()
    assert body["model_name"] in ("random_forest", "logistic_regression")
    assert body["feature_count"] == 19
    assert "roc_auc" in body["metrics"]


def test_dataset_stats(client):
    resp = client.get("/api/dataset/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_customers"] == 7043
    assert 0 < body["churn_rate"] < 1
    assert len(body["churn_by_contract"]) == 3
    assert body["churn_probability_distribution"]  # non-empty


def test_predict_happy_path(client, valid_customer):
    resp = client.post("/api/predict", json=valid_customer)
    assert resp.status_code == 200
    body = resp.json()
    assert body["prediction"] in ("churn", "no_churn")
    assert 0.0 <= body["churn_probability"] <= 1.0
    assert body["risk_level"] in ("low", "medium", "high")
    assert len(body["top_factors"]) > 0
    assert isinstance(body["explanation"], str) and body["explanation"]


def test_predict_high_risk_profile(client, valid_customer):
    # Short tenure, month-to-month, high charges, no support -> should be churn.
    resp = client.post("/api/predict", json=valid_customer)
    body = resp.json()
    assert body["prediction"] == "churn"
    assert body["churn_probability"] > 0.5


def test_predict_batch(client, valid_customer):
    second = copy.deepcopy(valid_customer)
    second.update({"tenure": 70, "Contract": "Two year", "MonthlyCharges": 25.0, "TotalCharges": 1700.0})
    resp = client.post("/api/predict/batch", json={"customers": [valid_customer, second]})
    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 2
    assert len(body["predictions"]) == 2


# ---- Validation / error handling ----

def test_predict_missing_field(client, valid_customer):
    bad = copy.deepcopy(valid_customer)
    del bad["tenure"]
    resp = client.post("/api/predict", json=bad)
    assert resp.status_code == 422


def test_predict_wrong_type(client, valid_customer):
    bad = copy.deepcopy(valid_customer)
    bad["tenure"] = "not-a-number"
    resp = client.post("/api/predict", json=bad)
    assert resp.status_code == 422


def test_predict_negative_tenure(client, valid_customer):
    bad = copy.deepcopy(valid_customer)
    bad["tenure"] = -5
    resp = client.post("/api/predict", json=bad)
    assert resp.status_code == 422


def test_predict_invalid_contract(client, valid_customer):
    bad = copy.deepcopy(valid_customer)
    bad["Contract"] = "Lifetime"
    resp = client.post("/api/predict", json=bad)
    assert resp.status_code == 422


def test_predict_invalid_payment_method(client, valid_customer):
    bad = copy.deepcopy(valid_customer)
    bad["PaymentMethod"] = "Bitcoin"
    resp = client.post("/api/predict", json=bad)
    assert resp.status_code == 422


def test_predict_extreme_monthly_charges(client, valid_customer):
    bad = copy.deepcopy(valid_customer)
    bad["MonthlyCharges"] = 99999.0
    resp = client.post("/api/predict", json=bad)
    assert resp.status_code == 422


def test_predict_unknown_field_rejected(client, valid_customer):
    bad = copy.deepcopy(valid_customer)
    bad["hacker_field"] = "oops"
    resp = client.post("/api/predict", json=bad)
    assert resp.status_code == 422


def test_predict_empty_batch(client):
    resp = client.post("/api/predict/batch", json={"customers": []})
    assert resp.status_code == 422
