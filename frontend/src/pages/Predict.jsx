import { useState } from 'react'
import { api } from '../services/api.js'
import PredictionForm from '../components/prediction/PredictionForm.jsx'
import PredictionResult from '../components/prediction/PredictionResult.jsx'
import { PageHeader } from '../components/ui/ChartCard.jsx'
import { Spinner } from '../components/ui/States.jsx'

export default function Predict() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (payload) => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.predict(payload)
      setResult(data)
    } catch (err) {
      setError(err.message || 'Prediction failed. Please try again.')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Customer Prediction"
        description="Enter a customer's details to estimate their churn risk and the factors behind it."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <div className="card p-6 lg:col-span-3">
          <PredictionForm onSubmit={handleSubmit} loading={loading} />
        </div>

        <div className="lg:col-span-2">
          {loading && (
            <div className="card flex flex-col items-center justify-center gap-3 p-10 text-center">
              <Spinner className="h-8 w-8" />
              <p className="text-sm font-medium text-slate-600">Analyzing customer…</p>
            </div>
          )}

          {!loading && error && (
            <div className="card border-red-200 bg-red-50 p-6">
              <p className="text-sm font-semibold text-red-700">Prediction failed</p>
              <p className="mt-1 text-sm text-red-600">{error}</p>
            </div>
          )}

          {!loading && !error && result && <PredictionResult result={result} />}

          {!loading && !error && !result && (
            <div className="card flex flex-col items-center justify-center gap-2 p-10 text-center text-slate-400">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="4" />
              </svg>
              <p className="text-sm">Submit the form to see a prediction.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
