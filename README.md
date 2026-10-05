# ChurnGuard — Customer Churn Prediction

An end-to-end, explainable machine-learning web application that predicts whether a
telecom customer is likely to churn. A React dashboard talks to a FastAPI +
scikit-learn backend, and the whole thing deploys as **one Vercel project with one
URL** — the React app at `/` and the API at `/api/*`.

> Prediction, probability, risk level, and the top factors behind each prediction
> all come from a real trained model — nothing is hardcoded.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Dataset](#dataset)
- [ML Approach](#ml-approach)
- [EDA](#eda)
- [Model Comparison & Metrics](#model-comparison--metrics)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment (Single Vercel Project)](#deployment-single-vercel-project)
- [Retraining the Model](#retraining-the-model)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)

---

## Features

- **Dashboard** with KPI cards and charts (churn split, churn by contract / tenure /
  payment method, monthly-charges distribution, predicted-probability distribution) —
  all computed from the real dataset and model.
- **Prediction form** with dependent-field logic (e.g. internet add-ons disable when
  there's no internet service) and client-side validation.
- **Explainable results**: churn Yes/No, probability, Low/Medium/High risk band, and
  the top contributing factors with direction (↑/↓ risk).
- **Model performance page**: side-by-side model comparison, metrics, confusion matrix.
- **Robust API**: health, model-info, dataset stats, single + batch prediction, with
  Pydantic validation and safe error handling.
- **Single-domain deployment** on Vercel (no separate backend URL).

---

## Architecture

```
Browser (React SPA)
      │  relative fetch:  /api/predict
      ▼
Vercel edge/router  ──(/api/*)──►  Python serverless function (api/index.py → FastAPI)
      │  (everything else)                     │
      ▼                                        ▼
Static assets (frontend/dist)         sklearn Pipeline (model/churn_pipeline.joblib)
                                               │
                                     preprocess → model → probability → explanation
```

The same FastAPI app runs locally (`uvicorn app.main:app`) and on Vercel (imported by
`api/index.py`). In development, the Vite dev server proxies `/api` to the local
FastAPI server, so the frontend uses identical relative paths in both environments.

---

## Tech Stack

| Layer      | Tools                                                             |
| ---------- | ---------------------------------------------------------------- |
| Frontend   | React 18, Vite, Tailwind CSS, Recharts, Axios, React Router      |
| Backend    | FastAPI, Pydantic v2, Uvicorn                                    |
| ML         | scikit-learn, pandas, NumPy, joblib; Matplotlib/Seaborn for EDA |
| Deployment | Vercel (static frontend + Python serverless function)           |

---

## Dataset

[IBM Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
(`data/telco_churn.csv`), 7,043 customers × 21 columns.

- **Target:** `Churn` (Yes/No). Class balance: **73.5% No / 26.5% Yes** (imbalanced).
- **Features used (19):** `gender`, `SeniorCitizen`, `Partner`, `Dependents`, `tenure`,
  `PhoneService`, `MultipleLines`, `InternetService`, `OnlineSecurity`, `OnlineBackup`,
  `DeviceProtection`, `TechSupport`, `StreamingTV`, `StreamingMovies`, `Contract`,
  `PaperlessBilling`, `PaymentMethod`, `MonthlyCharges`, `TotalCharges`.
- **Cleaning:** `TotalCharges` ships as text with blanks for brand-new customers
  (tenure = 0); it's coerced to numeric and those blanks set to 0. `customerID` is
  dropped.

---

## ML Approach

The full pipeline (`app/ml/`) is:

```
data → cleaning → preprocessing (ColumnTransformer) → train/test split
     → train LogisticRegression + RandomForest → evaluate → select best (ROC-AUC)
     → refit on full data → serialize pipeline + metrics + feature metadata
```

- **Single sklearn `Pipeline`** owns preprocessing + model, so training-time and
  inference-time preprocessing are guaranteed identical (no duplicated logic).
  - Numeric: median imputation + standard scaling.
  - Categorical: most-frequent imputation + one-hot encoding (`handle_unknown="ignore"`).
- **Class imbalance** handled with `class_weight="balanced"` on both models (no
  synthetic resampling), which is why recall is prioritised over raw accuracy.
- **Model selection** by **ROC-AUC** on a stratified 20% hold-out set — threshold
  independent and appropriate for imbalanced data.
- **Explainability** is model-based, per prediction:
  - Logistic Regression → signed `coefficient × standardized value` contributions.
  - Random Forest → "what-if" occlusion: each feature is set to a neutral baseline and
    the change in predicted probability is measured.
  - These describe **model feature importance for an input**, labeled as correlational
    associations — *not* causal claims.

---

## EDA

Run `python training/eda.py` to print a dataset summary and save figures to
`reports/figures/`. Key observations (computed, not fabricated):

- Churn is imbalanced: **26.5%** of customers churned.
- **Contract** is the strongest categorical signal: month-to-month churns at **42.7%**
  vs **2.8%** for two-year contracts.
- **Fiber-optic** internet customers churn at **41.9%** (vs 7.4% for no internet).
- **Electronic-check** payers churn at **45.3%**, far above automatic methods (~15–17%).
- Churn concentrates in **low-tenure** customers.

---

## Model Comparison & Metrics

Evaluated on the stratified hold-out test set (1,409 customers). Reproduced with
`python training/train.py`; your numbers may vary by a fraction due to library
versions.

| Model                   | Accuracy | Precision | Recall | F1     | ROC-AUC   |
| ----------------------- | -------- | --------- | ------ | ------ | --------- |
| Logistic Regression     | 0.738    | 0.504     | 0.783  | 0.614  | 0.8416    |
| **Random Forest** ✅    | **0.767**| **0.545** | 0.741  | **0.628** | **0.8417** |

**Selected model: Random Forest** (highest ROC-AUC; also better accuracy/precision/F1).
Confusion matrix (rows = actual, cols = predicted): `[[804, 231], [97, 277]]`.

The two models are extremely close on ROC-AUC — both are reasonable choices, and the
selection is made automatically by the training script rather than hand-picked.

---

## Project Structure

```
customer-churn-prediction/
├── api/
│   └── index.py              # Vercel serverless entry → imports app.main:app
├── app/                      # FastAPI application package (runs locally and on Vercel)
│   ├── main.py               # app, CORS, exception handlers, routers
│   ├── config.py             # env-driven settings, project-relative paths
│   ├── routes/               # health, predict, dataset endpoints
│   ├── schemas/              # Pydantic request/response models
│   ├── services/             # model_service, dataset_service, registry
│   ├── ml/                   # features, data, preprocessing, explain, train
│   └── utils/                # logging
├── model/                    # committed artifacts (churn_pipeline.joblib, *.json)
├── data/                     # telco_churn.csv
├── training/
│   ├── train.py              # `python training/train.py`
│   └── eda.py                # `python training/eda.py`
├── tests/                    # pytest: API + ML smoke tests
├── frontend/                 # React + Vite app
│   └── src/{pages,components,services,hooks,lib,test}
├── requirements.txt          # lean runtime deps (serverless)
├── requirements-dev.txt      # + uvicorn, matplotlib, seaborn, pytest
├── vercel.json               # single-project routing + includeFiles
├── package.json              # root build orchestration for Vercel
└── .env.example / .gitignore
```

---

## Local Setup

**Prerequisites:** Python 3.11+ and Node 18+.

### 1. Backend / ML

```bash
# from the repo root
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate

pip install -r requirements.txt -r requirements-dev.txt

# (Optional) retrain — a trained model is already committed in model/
python training/train.py

# Run the API
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000   (docs at http://localhost:8000/docs)
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173   (proxies /api to http://localhost:8000)
```

Open **http://localhost:5173**.

---

## Environment Variables

Everything works out of the box with no env file. Override only if needed.

**Backend** (`.env` at repo root — see `.env.example`):

| Variable       | Default                                             | Purpose                              |
| -------------- | --------------------------------------------------- | ------------------------------------ |
| `APP_NAME`     | `Churn Prediction API`                              | App title                            |
| `ENVIRONMENT`  | `development`                                        | Environment label                    |
| `LOG_LEVEL`    | `INFO`                                               | Logging level                        |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173`       | Allowed origins (only for cross-origin) |
| `MODEL_DIR`    | `./model`                                            | Model artifacts directory            |
| `DATA_PATH`    | `./data/telco_churn.csv`                             | Dataset path                         |

**Frontend** (`frontend/.env` — see `frontend/.env.example`):

| Variable             | Default               | Purpose                                            |
| -------------------- | --------------------- | -------------------------------------------------- |
| `VITE_API_URL`       | *(empty → relative)*  | Only set to target an API on a different origin    |
| `VITE_DEV_API_PROXY` | `http://localhost:8000` | Dev proxy target                                 |

---

## API Documentation

Base URL: `http://localhost:8000` locally, or `https://<your-project>.vercel.app` in
production. All endpoints are under `/api`.

| Method | Endpoint             | Description                               |
| ------ | -------------------- | ----------------------------------------- |
| GET    | `/api/health`        | Liveness + whether the model is loaded    |
| GET    | `/api/model-info`    | Model name, version, metrics, comparison  |
| GET    | `/api/dataset/stats` | Aggregate statistics for the dashboard    |
| POST   | `/api/predict`       | Predict churn for one customer            |
| POST   | `/api/predict/batch` | Predict churn for many customers          |

**Example — single prediction**

```bash
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "gender": "Female", "SeniorCitizen": 0, "Partner": "No", "Dependents": "No",
    "tenure": 2, "PhoneService": "Yes", "MultipleLines": "No",
    "InternetService": "Fiber optic", "OnlineSecurity": "No", "OnlineBackup": "No",
    "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "Yes",
    "StreamingMovies": "Yes", "Contract": "Month-to-month", "PaperlessBilling": "Yes",
    "PaymentMethod": "Electronic check", "MonthlyCharges": 95.0, "TotalCharges": 190.0
  }'
```

```json
{
  "prediction": "churn",
  "churn_probability": 0.9181,
  "risk_level": "high",
  "top_factors": [
    { "feature": "tenure", "value": 2, "description": "Customer tenure (months): 2 months", "direction": "increases", "weight": 1.0 }
  ],
  "explanation": "The model estimates this customer is likely to churn (high risk). ..."
}
```

**Status codes:** `200` success · `422` validation error · `503` model/dataset
unavailable · `500` unexpected error. Stack traces are never returned to clients.

---

## Testing

**Backend (pytest)** — API endpoints, validation, and ML smoke tests:

```bash
# from the repo root (with dev deps installed)
pytest
```

Covers: health, model-info, dataset stats, single & batch predict, and invalid input
(missing field, wrong type, negative tenure, invalid contract/payment method, extreme
charges, unknown field, empty batch), plus model load / probability-range / feature
-metadata / explanation checks.

**Frontend (Vitest + React Testing Library)**:

```bash
cd frontend
npm test
```

Covers: form rendering, validation, payload shape, reset, and the full predict flow
(request sent → result rendered → API error handled).

---

## Deployment (Single Vercel Project)

The entire repo deploys as **one Vercel project**. The React app is served at `/`
and the FastAPI backend at `/api/*` — no separate backend deployment, no second URL.

### How it's wired

- `vercel.json` builds the frontend (`frontend/dist`) and routes:
  - `/api/(.*)` → the Python serverless function `api/index.py` (the FastAPI app),
  - everything else → the SPA's `index.html` (client-side routing).
- `includeFiles` bundles `app/`, `model/`, and `data/` with the function so the model
  and dataset are available at runtime.
- The frontend calls relative `/api/*` paths, so **no `VITE_API_URL` is needed** in
  production.

### Steps

1. **Push to GitHub** (see below).
2. Go to **[vercel.com](https://vercel.com) → Add New → Project** and **import** the
   repository.
3. Leave the framework preset as **Other**. The settings come from `vercel.json`:
   - Build Command: `cd frontend && npm install && npm run build`
   - Output Directory: `frontend/dist`
   - (No install command or root changes needed.)
4. **Environment variables:** none required for the default single-domain setup.
5. Click **Deploy**.
6. Verify:
   - `https://<your-project>.vercel.app/` → dashboard loads
   - `https://<your-project>.vercel.app/api/health` → `{"status":"ok","model_loaded":true}`
   - Make a prediction from the UI.

> **Python runtime:** Vercel's Python runtime (3.12) runs the FastAPI app via the
> module-level `app` ASGI object in `api/index.py`.

### Deployment limits & why this fits

Vercel serverless functions have a bundle size limit (**250 MB unzipped**). This project
is built to stay within it:

- The committed model is compressed to **~4 MB** (`joblib compress=3`).
- `requirements.txt` is **lean** (fastapi, pydantic, pandas, numpy, scikit-learn,
  joblib). Heavy, inference-irrelevant packages (matplotlib, seaborn, uvicorn, pytest)
  live only in `requirements-dev.txt` and are **not** deployed.

If a future change pushes the bundle over the limit (e.g. adding large libraries), the
cold-start/size trade-off can be addressed by trimming dependencies first. Only if
Vercel genuinely cannot host the function would a standalone API host be needed — in
that case, set `VITE_API_URL` in Vercel to the external API origin (the frontend
already supports it) and host `app/` with `uvicorn app.main:app`. This is **not**
required for the current project.

---

## Retraining the Model

```bash
python training/train.py
```

This loads and cleans the dataset, trains both models, evaluates them, selects the best
by ROC-AUC, refits it on the full dataset, and writes `model/churn_pipeline.joblib`,
`model/metrics.json`, and `model/feature_metadata.json`. Commit the updated artifacts to
redeploy a new model.

---

## Troubleshooting

| Symptom                                    | Fix                                                                 |
| ------------------------------------------ | ------------------------------------------------------------------- |
| `model_loaded: false` / 503 on predict     | Run `python training/train.py` so `model/churn_pipeline.joblib` exists. |
| Frontend can't reach API in dev            | Ensure the API runs on port 8000, or set `VITE_DEV_API_PROXY`.      |
| CORS error in dev                          | Add your frontend origin to `CORS_ORIGINS` (the dev proxy avoids this). |
| `npm install` EPERM on Windows             | Close editors/AV locking `node_modules`, delete it, reinstall.      |
| 422 on prediction                          | A field is missing/out of range — check the response `errors` array. |

---

## Future Improvements

- SHAP-based explanations for a unified, theoretically-grounded attribution method.
- Threshold tuning UI to trade off precision vs recall per business cost.
- Model monitoring / drift detection and scheduled retraining.
- Persisted prediction history and CSV upload for batch scoring in the UI.

---

*Built as a portfolio-quality, end-to-end ML application. Predictions and statistics
are generated by the trained model and dataset — not mocked.*
