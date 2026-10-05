import { useCallback } from 'react'
import { api } from '../services/api.js'
import useFetch from '../hooks/useFetch.js'
import ChartCard, { PageHeader } from '../components/ui/ChartCard.jsx'
import { Loading, ErrorState } from '../components/ui/States.jsx'
import { formatNumber, formatPercent, titleCase } from '../lib/format.js'

const METRIC_KEYS = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
const METRIC_LABELS = {
  accuracy: 'Accuracy',
  precision: 'Precision',
  recall: 'Recall',
  f1: 'F1 Score',
  roc_auc: 'ROC-AUC',
}

export default function ModelPerformance() {
  const fetcher = useCallback(() => api.modelInfo(), [])
  const { data, loading, error, refetch } = useFetch(fetcher)

  if (loading) return <Loading label="Loading model performance…" />
  if (error) return <ErrorState message={error} onRetry={refetch} />

  const models = Object.entries(data.all_models || {})
  const selected = data.model_name
  const cm = data.metrics?.confusion_matrix

  return (
    <div>
      <PageHeader
        title="Model Performance"
        description="How the candidate models were evaluated and which one was selected for production."
      />

      {/* Summary banner */}
      <div className="card mb-6 flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-slate-500">Production model</p>
          <p className="text-xl font-bold text-slate-900">{titleCase(selected)}</p>
          <p className="mt-1 text-xs text-slate-400">
            Selected by {data.selection_metric.toUpperCase()} · version {data.model_version} · trained {data.trained_on}
          </p>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center sm:grid-cols-3">
          <Stat label="Features" value={data.feature_count} />
          <Stat label="Train rows" value={formatNumber(data.dataset?.train_rows)} />
          <Stat label="Test rows" value={formatNumber(data.dataset?.test_rows)} />
        </div>
      </div>

      {/* Comparison table */}
      <ChartCard title="Model Comparison" subtitle="Metrics on the held-out test set" className="mb-6">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-4 font-medium">Model</th>
                {METRIC_KEYS.map((k) => (
                  <th key={k} className="px-3 py-2 font-medium">{METRIC_LABELS[k]}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {models.map(([name, m]) => {
                const isSelected = name === selected
                return (
                  <tr
                    key={name}
                    className={`border-b border-slate-100 ${isSelected ? 'bg-brand-50/50' : ''}`}
                  >
                    <td className="py-3 pr-4 font-medium text-slate-800">
                      {titleCase(name)}
                      {isSelected && (
                        <span className="ml-2 rounded-full bg-brand-600 px-2 py-0.5 text-[10px] font-semibold text-white">
                          SELECTED
                        </span>
                      )}
                    </td>
                    {METRIC_KEYS.map((k) => (
                      <td key={k} className="px-3 py-3 tabular-nums text-slate-600">
                        {m[k] != null ? m[k].toFixed(3) : '—'}
                      </td>
                    ))}
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </ChartCard>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Selected model metric cards */}
        <ChartCard title={`${titleCase(selected)} — Key Metrics`}>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {METRIC_KEYS.map((k) => (
              <div key={k} className="rounded-lg border border-slate-200 p-4 text-center">
                <p className="text-xs font-medium text-slate-500">{METRIC_LABELS[k]}</p>
                <p className="mt-1 text-xl font-bold text-brand-600">
                  {data.metrics?.[k] != null
                    ? k === 'roc_auc'
                      ? data.metrics[k].toFixed(3)
                      : formatPercent(data.metrics[k])
                    : '—'}
                </p>
              </div>
            ))}
          </div>
        </ChartCard>

        {/* Confusion matrix */}
        <ChartCard title="Confusion Matrix" subtitle="Rows: actual · Columns: predicted">
          {cm ? (
            <ConfusionMatrix cm={cm} />
          ) : (
            <p className="py-10 text-center text-sm text-slate-400">Not available.</p>
          )}
        </ChartCard>
      </div>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div>
      <p className="text-lg font-bold text-slate-900">{value ?? '—'}</p>
      <p className="text-xs text-slate-400">{label}</p>
    </div>
  )
}

function ConfusionMatrix({ cm }) {
  // cm = [[TN, FP], [FN, TP]]
  const [[tn, fp], [fn, tp]] = cm
  const cell = (val, label, tone) => (
    <div className={`rounded-lg p-4 text-center ${tone}`}>
      <p className="text-2xl font-bold">{val.toLocaleString()}</p>
      <p className="mt-0.5 text-xs opacity-80">{label}</p>
    </div>
  )
  return (
    <div className="grid grid-cols-2 gap-3">
      {cell(tn, 'True Negative', 'bg-emerald-50 text-emerald-700')}
      {cell(fp, 'False Positive', 'bg-amber-50 text-amber-700')}
      {cell(fn, 'False Negative', 'bg-amber-50 text-amber-700')}
      {cell(tp, 'True Positive', 'bg-emerald-50 text-emerald-700')}
    </div>
  )
}
