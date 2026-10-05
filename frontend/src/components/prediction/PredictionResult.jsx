import { formatPercent, riskStyles } from '../../lib/format.js'

export default function PredictionResult({ result }) {
  const risk = riskStyles[result.risk_level] || riskStyles.low
  const willChurn = result.prediction === 'churn'
  const pct = result.churn_probability

  const increasing = result.top_factors.filter((f) => f.direction === 'increases')
  const decreasing = result.top_factors.filter((f) => f.direction === 'decreases')

  return (
    <div className="space-y-5">
      {/* Headline card */}
      <div className={`card p-6 ring-1 ${risk.ring} ${risk.bg}`}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Customer Churn Risk
            </p>
            <p className={`mt-1 text-2xl font-bold ${risk.text}`}>{risk.label}</p>
            <p className="mt-1 text-sm text-slate-600">
              {willChurn ? 'Likely to churn' : 'Likely to stay'}
            </p>
          </div>
          <div className="text-right">
            <p className={`text-4xl font-extrabold tracking-tight ${risk.text}`}>
              {formatPercent(pct)}
            </p>
            <p className="text-xs text-slate-500">probability of churn</p>
          </div>
        </div>

        {/* Probability bar */}
        <div className="mt-5">
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/70">
            <div
              className={`h-full rounded-full ${risk.bar} transition-all`}
              style={{ width: `${Math.round(pct * 100)}%` }}
            />
          </div>
          <div className="mt-1 flex justify-between text-[11px] text-slate-400">
            <span>0%</span><span>50%</span><span>100%</span>
          </div>
        </div>
      </div>

      {/* Contributing factors */}
      <div className="card p-6">
        <h3 className="text-sm font-semibold text-slate-800">Top contributing factors</h3>
        <p className="mt-0.5 text-xs text-slate-400">
          Model feature importance for this customer — associations the model learned, not proven causes.
        </p>

        <ol className="mt-4 space-y-3">
          {result.top_factors.map((f, i) => (
            <li key={f.feature} className="flex items-center gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm text-slate-700">{f.description}</span>
                  <span
                    className={`shrink-0 text-xs font-medium ${
                      f.direction === 'increases' ? 'text-red-600' : 'text-emerald-600'
                    }`}
                  >
                    {f.direction === 'increases' ? '↑ risk' : '↓ risk'}
                  </span>
                </div>
                <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className={`h-full rounded-full ${
                      f.direction === 'increases' ? 'bg-red-400' : 'bg-emerald-400'
                    }`}
                    style={{ width: `${Math.max(6, Math.round(f.weight * 100))}%` }}
                  />
                </div>
              </div>
            </li>
          ))}
        </ol>

        <p className="mt-5 rounded-lg bg-slate-50 p-3 text-xs leading-relaxed text-slate-600">
          {result.explanation}
        </p>

        {increasing.length > 0 && decreasing.length > 0 && (
          <p className="mt-3 text-xs text-slate-400">
            {increasing.length} factor(s) raising risk · {decreasing.length} lowering risk
          </p>
        )}
      </div>
    </div>
  )
}
