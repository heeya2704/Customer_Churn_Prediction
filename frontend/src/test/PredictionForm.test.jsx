import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import PredictionForm from '../components/prediction/PredictionForm.jsx'

describe('PredictionForm', () => {
  it('renders key fields', () => {
    render(<PredictionForm onSubmit={vi.fn()} loading={false} />)
    expect(screen.getByLabelText(/Tenure/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Contract/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /predict churn/i })).toBeInTheDocument()
  })

  it('submits a well-formed payload with defaults', () => {
    const onSubmit = vi.fn()
    render(<PredictionForm onSubmit={onSubmit} loading={false} />)
    fireEvent.click(screen.getByRole('button', { name: /predict churn/i }))
    expect(onSubmit).toHaveBeenCalledTimes(1)
    const payload = onSubmit.mock.calls[0][0]
    expect(typeof payload.tenure).toBe('number')
    expect(payload.Contract).toBeTruthy()
    expect(payload).toHaveProperty('MonthlyCharges')
  })

  it('shows a validation error for an out-of-range tenure', () => {
    const onSubmit = vi.fn()
    render(<PredictionForm onSubmit={onSubmit} loading={false} />)
    fireEvent.change(screen.getByLabelText(/Tenure/i), { target: { value: '999' } })
    fireEvent.click(screen.getByRole('button', { name: /predict churn/i }))
    expect(onSubmit).not.toHaveBeenCalled()
    expect(screen.getByText(/between 0 and 120/i)).toBeInTheDocument()
  })

  it('resets the form', () => {
    render(<PredictionForm onSubmit={vi.fn()} loading={false} />)
    const tenure = screen.getByLabelText(/Tenure/i)
    fireEvent.change(tenure, { target: { value: '42' } })
    expect(tenure.value).toBe('42')
    fireEvent.click(screen.getByRole('button', { name: /reset form/i }))
    expect(tenure.value).toBe('5')
  })
})
