import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import Predict from '../pages/Predict.jsx'
import { api } from '../services/api.js'

vi.mock('../services/api.js', () => ({
  api: { predict: vi.fn() },
}))

const SAMPLE_RESULT = {
  prediction: 'churn',
  churn_probability: 0.78,
  risk_level: 'high',
  explanation: 'The model estimates this customer is likely to churn (high risk).',
  top_factors: [
    { feature: 'Contract', value: 'Month-to-month', description: 'Month-to-month contract', direction: 'increases', weight: 1 },
    { feature: 'tenure', value: 5, description: 'Customer tenure (months): 5 months', direction: 'increases', weight: 0.6 },
  ],
}

describe('Predict page flow', () => {
  beforeEach(() => vi.clearAllMocks())

  it('sends a prediction request and renders the result', async () => {
    api.predict.mockResolvedValueOnce(SAMPLE_RESULT)
    render(<Predict />)

    fireEvent.click(screen.getByRole('button', { name: /predict churn/i }))

    await waitFor(() => expect(api.predict).toHaveBeenCalledTimes(1))
    // Exact match targets the risk-label heading specifically (the explanation
    // text also contains the words "high risk").
    expect(await screen.findByText('High Risk')).toBeInTheDocument()
    expect(screen.getByText(/78.0%/)).toBeInTheDocument()
    expect(screen.getByText(/Month-to-month contract/i)).toBeInTheDocument()
  })

  it('shows an error state when the API fails', async () => {
    api.predict.mockRejectedValueOnce({ message: 'Unable to reach the prediction service. Please try again.' })
    render(<Predict />)

    fireEvent.click(screen.getByRole('button', { name: /predict churn/i }))

    expect(await screen.findByText(/Unable to reach the prediction service/i)).toBeInTheDocument()
  })
})
