import { PageHeader } from '../components/ui/ChartCard.jsx'

export default function About() {
  return (
    <div className="max-w-3xl">
      <PageHeader
        title="About this project"
        description="An end-to-end, explainable machine-learning application for telecom customer churn."
      />

      <div className="space-y-5">
        <Section title="What it does">
          <p>
            ChurnGuard predicts whether a telecom customer is likely to churn, how
            confident the model is, and which of the customer's attributes most
            influenced the prediction. It pairs a FastAPI + scikit-learn backend
            with a React dashboard, deployed together as a single application.
          </p>
        </Section>

        <Section title="The data">
          <p>
            Trained on the public{' '}
            <a
              className="text-brand-600 underline"
              href="https://www.kaggle.com/datasets/blastchar/telco-customer-churn"
              target="_blank"
              rel="noreferrer"
            >
              IBM Telco Customer Churn
            </a>{' '}
            dataset (7,043 customers, 19 features). Roughly 26.5% of customers in
            the dataset churned, so the models are trained with balanced class
            weights to handle this imbalance.
          </p>
        </Section>

        <Section title="The model">
          <p>
            Two models — Logistic Regression and Random Forest — are trained inside
            a single scikit-learn pipeline that owns all preprocessing
            (imputation, scaling, one-hot encoding). The better model by ROC-AUC on
            a held-out test set is selected and serialized for production, so the
            exact same preprocessing runs at training and inference time.
          </p>
        </Section>

        <Section title="How to read the explanation">
          <p>
            Contributing factors describe <strong>model feature importance for a
            specific customer</strong> — the attributes most associated with the
            model's score. They are correlational signals the model learned, not
            proven causes of churn, and should be read as such.
          </p>
        </Section>

        <Section title="Tech stack">
          <ul className="list-inside list-disc space-y-1">
            <li>Frontend: React, Vite, Tailwind CSS, Recharts, Axios</li>
            <li>Backend: FastAPI, Pydantic, scikit-learn, pandas, joblib</li>
            <li>Deployment: a single Vercel project (static frontend + Python serverless API)</li>
          </ul>
        </Section>
      </div>
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="card p-6">
      <h2 className="mb-2 text-base font-semibold text-slate-900">{title}</h2>
      <div className="text-sm leading-relaxed text-slate-600">{children}</div>
    </div>
  )
}
