import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import Dashboard from '../pages/Dashboard.jsx'
import ModelPerformance from '../pages/ModelPerformance.jsx'
import { api } from '../services/api.js'

vi.mock('../services/api.js', () => ({
  api: { datasetStats: vi.fn(), modelInfo: vi.fn(), health: vi.fn() },
}))

const STATS = {
  total_customers: 7043,
  churned: 1869,
  retained: 5174,
  churn_rate: 0.2654,
  retention_rate: 0.7346,
  avg_monthly_charges: 64.76,
  avg_tenure: 32.4,
  churn_by_contract: [
    { category: 'Month-to-month', total: 3875, churned: 1655, churn_rate: 0.4271 },
    { category: 'One year', total: 1473, churned: 166, churn_rate: 0.1127 },
    { category: 'Two year', total: 1695, churned: 48, churn_rate: 0.0283 },
  ],
  churn_by_payment_method: [
    { category: 'Electronic check', total: 2365, churned: 1071, churn_rate: 0.4528 },
  ],
  churn_by_internet_service: [
    { category: 'DSL', total: 2421, churned: 459, churn_rate: 0.1896 },
  ],
  churn_by_tenure: [
    { category: '0-12', total: 2175, churned: 1037, churn_rate: 0.4768 },
    { category: '60+', total: 1407, churned: 95, churn_rate: 0.0675 },
  ],
  monthly_charges_distribution: [
    { range: '$0-$20', churned: 10, retained: 500 },
    { range: '$80-$100', churned: 400, retained: 600 },
  ],
  churn_probability_distribution: [
    { range: '0-10%', count: 2000 },
    { range: '90-100%', count: 120 },
  ],
}

const MODEL_INFO = {
  model_name: 'random_forest',
  model_version: '1.0.0',
  trained_on: '2026-10-05',
  selection_metric: 'roc_auc',
  feature_count: 19,
  metrics: {
    accuracy: 0.7672,
    precision: 0.5453,
    recall: 0.7406,
    f1: 0.6281,
    roc_auc: 0.8417,
    confusion_matrix: [[804, 231], [97, 277]],
  },
  all_models: {
    logistic_regression: { accuracy: 0.7381, precision: 0.5043, recall: 0.7834, f1: 0.6136, roc_auc: 0.8416 },
    random_forest: { accuracy: 0.7672, precision: 0.5453, recall: 0.7406, f1: 0.6281, roc_auc: 0.8417 },
  },
  dataset: { total_rows: 7043, train_rows: 5634, test_rows: 1409, churn_rate: 0.2654 },
}

describe('Dashboard page', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders KPIs and charts from real-shaped data', async () => {
    api.datasetStats.mockResolvedValueOnce(STATS)
    api.modelInfo.mockResolvedValueOnce(MODEL_INFO)
    render(<MemoryRouter><Dashboard /></MemoryRouter>)

    expect(await screen.findByText('Total Customers')).toBeInTheDocument()
    expect(screen.getByText('7,043')).toBeInTheDocument()
    expect(screen.getByText('26.5%')).toBeInTheDocument() // churn rate
    expect(screen.getByText('Churn Rate by Contract')).toBeInTheDocument()
  })

  it('shows an error state when stats fail', async () => {
    api.datasetStats.mockRejectedValueOnce({ message: 'boom' })
    api.modelInfo.mockResolvedValueOnce(MODEL_INFO)
    render(<MemoryRouter><Dashboard /></MemoryRouter>)
    expect(await screen.findByText('boom')).toBeInTheDocument()
  })
})

describe('ModelPerformance page', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the comparison table and confusion matrix', async () => {
    api.modelInfo.mockResolvedValueOnce(MODEL_INFO)
    render(<MemoryRouter><ModelPerformance /></MemoryRouter>)

    expect(await screen.findByText('Model Comparison')).toBeInTheDocument()
    expect(screen.getByText('SELECTED')).toBeInTheDocument()
    expect(screen.getByText('Confusion Matrix')).toBeInTheDocument()
    expect(screen.getByText('804')).toBeInTheDocument() // TN cell
  })
})
