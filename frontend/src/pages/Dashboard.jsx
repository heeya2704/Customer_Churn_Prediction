import { useCallback } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from '../services/api.js'
import useFetch from '../hooks/useFetch.js'
import Kpi from '../components/ui/Kpi.jsx'
import ChartCard, { PageHeader } from '../components/ui/ChartCard.jsx'
import { Loading, ErrorState } from '../components/ui/States.jsx'
import { formatNumber, formatPercent } from '../lib/format.js'

const COLORS = {
  churn: '#ef4444',
  retain: '#10b981',
  bar: '#2563eb',
  bar2: '#93c5fd',
  rate: '#f59e0b',
}

export default function Dashboard() {
  const fetchAll = useCallback(
    () => Promise.all([api.datasetStats(), api.modelInfo().catch(() => null)]),
    [],
  )
  const { data, loading, error, refetch } = useFetch(fetchAll)

  if (loading) return <Loading label="Loading dashboard…" />
  if (error) return <ErrorState message={error} onRetry={refetch} />

  const [stats, model] = data
  const metrics = model?.metrics || {}

  const churnSplit = [
    { name: 'Churned', value: stats.churned, color: COLORS.churn },
    { name: 'Retained', value: stats.retained, color: COLORS.retain },
  ]

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Churn patterns across the telecom customer base, derived from the training dataset."
      />

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <Kpi label="Total Customers" value={formatNumber(stats.total_customers)} accent="brand" />
        <Kpi label="Churn Rate" value={formatPercent(stats.churn_rate)} accent="red" />
        <Kpi label="Retention Rate" value={formatPercent(stats.retention_rate)} accent="emerald" />
        <Kpi
          label="Model Accuracy"
          value={metrics.accuracy != null ? formatPercent(metrics.accuracy) : '—'}
          accent="slate"
        />
        <Kpi
          label="ROC-AUC"
          value={metrics.roc_auc != null ? metrics.roc_auc.toFixed(3) : '—'}
          accent="amber"
        />
      </div>

      {/* Charts */}
      <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <ChartCard title="Churn vs Retained" subtitle="Overall class balance">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={churnSplit}
                dataKey="value"
                nameKey="name"
                innerRadius={60}
                outerRadius={95}
                paddingAngle={2}
              >
                {churnSplit.map((entry) => (
                  <Cell key={entry.name} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => formatNumber(v)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Churn Rate by Contract" subtitle="Share of customers who churned">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={toRate(stats.churn_by_contract)} margin={{ left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eef2f7" />
              <XAxis dataKey="category" fontSize={12} tickLine={false} />
              <YAxis fontSize={12} tickFormatter={(v) => `${v}%`} tickLine={false} axisLine={false} />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="rate" fill={COLORS.bar} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Churn Rate by Tenure" subtitle="Months as a customer">
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={toRate(stats.churn_by_tenure)} margin={{ left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f7" />
              <XAxis dataKey="category" fontSize={12} tickLine={false} />
              <YAxis fontSize={12} tickFormatter={(v) => `${v}%`} tickLine={false} axisLine={false} />
              <Tooltip formatter={(v) => `${v}%`} />
              <Line type="monotone" dataKey="rate" stroke={COLORS.rate} strokeWidth={2.5} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Churn Rate by Payment Method">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              data={toRate(stats.churn_by_payment_method)}
              layout="vertical"
              margin={{ left: 40 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#eef2f7" />
              <XAxis type="number" fontSize={12} tickFormatter={(v) => `${v}%`} tickLine={false} />
              <YAxis
                type="category"
                dataKey="category"
                fontSize={11}
                width={120}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip formatter={(v) => `${v}%`} />
              <Bar dataKey="rate" fill={COLORS.bar} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Monthly Charges Distribution" subtitle="Churned vs retained by charge band">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={stats.monthly_charges_distribution} margin={{ left: -10 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eef2f7" />
              <XAxis dataKey="range" fontSize={11} tickLine={false} />
              <YAxis fontSize={12} tickLine={false} axisLine={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="retained" stackId="a" fill={COLORS.retain} name="Retained" />
              <Bar dataKey="churned" stackId="a" fill={COLORS.churn} name="Churned" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard
          title="Predicted Churn Probability"
          subtitle="Model scores across the full dataset"
        >
          {stats.churn_probability_distribution?.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={stats.churn_probability_distribution} margin={{ left: -10 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#eef2f7" />
                <XAxis dataKey="range" fontSize={10} tickLine={false} interval={0} angle={-30} textAnchor="end" height={50} />
                <YAxis fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip formatter={(v) => formatNumber(v)} />
                <Bar dataKey="count" fill={COLORS.bar2} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-16 text-center text-sm text-slate-400">
              Probability distribution unavailable (model not loaded).
            </p>
          )}
        </ChartCard>
      </div>
    </div>
  )
}

// Convert churn_rate (0..1) into a whole-number percentage for charts.
function toRate(rows = []) {
  return rows.map((r) => ({ ...r, rate: Math.round(r.churn_rate * 1000) / 10 }))
}
