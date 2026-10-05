// Small formatting helpers shared across the UI.

export const formatPercent = (value, digits = 1) =>
  value == null ? '—' : `${(value * 100).toFixed(digits)}%`

export const formatNumber = (value) =>
  value == null ? '—' : value.toLocaleString('en-US')

export const formatCurrency = (value) =>
  value == null ? '—' : `$${Number(value).toFixed(2)}`

export const titleCase = (str) =>
  str ? str.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) : str

// Consistent colors for risk levels across the app.
export const riskStyles = {
  low: { label: 'Low Risk', text: 'text-emerald-700', bg: 'bg-emerald-50', ring: 'ring-emerald-200', bar: 'bg-emerald-500' },
  medium: { label: 'Medium Risk', text: 'text-amber-700', bg: 'bg-amber-50', ring: 'ring-amber-200', bar: 'bg-amber-500' },
  high: { label: 'High Risk', text: 'text-red-700', bg: 'bg-red-50', ring: 'ring-red-200', bar: 'bg-red-500' },
}
