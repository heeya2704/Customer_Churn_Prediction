import { useMemo, useState } from 'react'

// Default represents a plausible at-risk customer so the form is ready to submit.
export const DEFAULT_FORM = {
  gender: 'Female',
  SeniorCitizen: 0,
  Partner: 'No',
  Dependents: 'No',
  tenure: 5,
  PhoneService: 'Yes',
  MultipleLines: 'No',
  InternetService: 'Fiber optic',
  OnlineSecurity: 'No',
  OnlineBackup: 'No',
  DeviceProtection: 'No',
  TechSupport: 'No',
  StreamingTV: 'Yes',
  StreamingMovies: 'Yes',
  Contract: 'Month-to-month',
  PaperlessBilling: 'Yes',
  PaymentMethod: 'Electronic check',
  MonthlyCharges: 89.9,
  TotalCharges: 449.5,
}

const YES_NO = ['Yes', 'No']
const ADDON = ['Yes', 'No', 'No internet service']

const SELECT_FIELDS = [
  { name: 'gender', label: 'Gender', options: ['Female', 'Male'] },
  { name: 'Partner', label: 'Partner', options: YES_NO },
  { name: 'Dependents', label: 'Dependents', options: YES_NO },
  { name: 'PhoneService', label: 'Phone Service', options: YES_NO },
  { name: 'MultipleLines', label: 'Multiple Lines', options: ['Yes', 'No', 'No phone service'] },
  { name: 'InternetService', label: 'Internet Service', options: ['DSL', 'Fiber optic', 'No'] },
  { name: 'OnlineSecurity', label: 'Online Security', options: ADDON },
  { name: 'OnlineBackup', label: 'Online Backup', options: ADDON },
  { name: 'DeviceProtection', label: 'Device Protection', options: ADDON },
  { name: 'TechSupport', label: 'Tech Support', options: ADDON },
  { name: 'StreamingTV', label: 'Streaming TV', options: ADDON },
  { name: 'StreamingMovies', label: 'Streaming Movies', options: ADDON },
  { name: 'Contract', label: 'Contract', options: ['Month-to-month', 'One year', 'Two year'] },
  { name: 'PaperlessBilling', label: 'Paperless Billing', options: YES_NO },
  {
    name: 'PaymentMethod',
    label: 'Payment Method',
    options: [
      'Electronic check',
      'Mailed check',
      'Bank transfer (automatic)',
      'Credit card (automatic)',
    ],
  },
]

const NUMERIC_FIELDS = [
  { name: 'tenure', label: 'Tenure (months)', min: 0, max: 120, step: 1 },
  { name: 'MonthlyCharges', label: 'Monthly Charges ($)', min: 0, max: 1000, step: 0.05 },
  { name: 'TotalCharges', label: 'Total Charges ($)', min: 0, max: 100000, step: 0.05 },
]

function validate(form) {
  const errors = {}
  for (const f of NUMERIC_FIELDS) {
    const v = form[f.name]
    if (v === '' || v === null || Number.isNaN(Number(v))) {
      errors[f.name] = 'Enter a number'
    } else if (Number(v) < f.min || Number(v) > f.max) {
      errors[f.name] = `Must be between ${f.min} and ${f.max}`
    }
  }
  return errors
}

export default function PredictionForm({ onSubmit, loading }) {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [errors, setErrors] = useState({})

  // Keep dependent fields consistent with the dataset's encoding.
  const noInternet = form.InternetService === 'No'
  const noPhone = form.PhoneService === 'No'

  const derivedForm = useMemo(() => {
    const next = { ...form }
    if (noInternet) {
      for (const name of [
        'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
        'TechSupport', 'StreamingTV', 'StreamingMovies',
      ]) {
        next[name] = 'No internet service'
      }
    }
    if (noPhone) next.MultipleLines = 'No phone service'
    return next
  }, [form, noInternet, noPhone])

  const setField = (name, value) => {
    setForm((prev) => ({ ...prev, [name]: value }))
    setErrors((prev) => ({ ...prev, [name]: undefined }))
  }

  const isDisabled = (name) => {
    if (name === 'MultipleLines' && noPhone) return true
    if (
      noInternet &&
      ['OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies'].includes(name)
    ) {
      return true
    }
    return false
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const found = validate(derivedForm)
    setErrors(found)
    if (Object.keys(found).length > 0) return
    const payload = {
      ...derivedForm,
      SeniorCitizen: Number(derivedForm.SeniorCitizen),
      tenure: Number(derivedForm.tenure),
      MonthlyCharges: Number(derivedForm.MonthlyCharges),
      TotalCharges: Number(derivedForm.TotalCharges),
    }
    onSubmit(payload)
  }

  const handleReset = () => {
    setForm(DEFAULT_FORM)
    setErrors({})
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      {/* Account details */}
      <fieldset className="mb-6">
        <legend className="mb-3 text-sm font-semibold text-slate-800">Account</legend>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {NUMERIC_FIELDS.map((f) => (
            <div key={f.name}>
              <label htmlFor={f.name} className="form-label">{f.label}</label>
              <input
                id={f.name}
                name={f.name}
                type="number"
                min={f.min}
                max={f.max}
                step={f.step}
                value={form[f.name]}
                onChange={(e) => setField(f.name, e.target.value)}
                className={`form-input ${errors[f.name] ? 'form-input-error' : ''}`}
                aria-invalid={Boolean(errors[f.name])}
              />
              {errors[f.name] && (
                <p className="mt-1 text-xs text-red-600">{errors[f.name]}</p>
              )}
            </div>
          ))}

          <div>
            <label htmlFor="Contract" className="form-label">Contract</label>
            <SelectControl name="Contract" value={form.Contract} onChange={setField}
              options={['Month-to-month', 'One year', 'Two year']} />
          </div>
          <div>
            <label htmlFor="PaymentMethod" className="form-label">Payment Method</label>
            <SelectControl name="PaymentMethod" value={form.PaymentMethod} onChange={setField}
              options={SELECT_FIELDS.find((s) => s.name === 'PaymentMethod').options} />
          </div>
          <div>
            <label htmlFor="PaperlessBilling" className="form-label">Paperless Billing</label>
            <SelectControl name="PaperlessBilling" value={form.PaperlessBilling} onChange={setField} options={YES_NO} />
          </div>
        </div>
      </fieldset>

      {/* Demographics */}
      <fieldset className="mb-6">
        <legend className="mb-3 text-sm font-semibold text-slate-800">Customer profile</legend>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label htmlFor="gender" className="form-label">Gender</label>
            <SelectControl name="gender" value={form.gender} onChange={setField} options={['Female', 'Male']} />
          </div>
          <ToggleControl
            name="SeniorCitizen"
            label="Senior Citizen"
            checked={Number(form.SeniorCitizen) === 1}
            onChange={(checked) => setField('SeniorCitizen', checked ? 1 : 0)}
          />
          <div>
            <label htmlFor="Partner" className="form-label">Partner</label>
            <SelectControl name="Partner" value={form.Partner} onChange={setField} options={YES_NO} />
          </div>
          <div>
            <label htmlFor="Dependents" className="form-label">Dependents</label>
            <SelectControl name="Dependents" value={form.Dependents} onChange={setField} options={YES_NO} />
          </div>
        </div>
      </fieldset>

      {/* Services */}
      <fieldset className="mb-6">
        <legend className="mb-3 text-sm font-semibold text-slate-800">Services</legend>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {SELECT_FIELDS.filter((f) =>
            ['PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies'].includes(f.name),
          ).map((f) => (
            <div key={f.name}>
              <label htmlFor={f.name} className="form-label">{f.label}</label>
              <SelectControl
                name={f.name}
                value={derivedForm[f.name]}
                onChange={setField}
                options={f.options}
                disabled={isDisabled(f.name)}
              />
            </div>
          ))}
        </div>
      </fieldset>

      <div className="flex flex-col gap-3 sm:flex-row">
        <button type="submit" className="btn-primary sm:w-48" disabled={loading}>
          {loading ? 'Analyzing customer…' : 'Predict churn'}
        </button>
        <button type="button" className="btn-secondary" onClick={handleReset} disabled={loading}>
          Reset form
        </button>
      </div>
    </form>
  )
}

function SelectControl({ name, value, onChange, options, disabled = false }) {
  return (
    <select
      id={name}
      name={name}
      value={value}
      disabled={disabled}
      onChange={(e) => onChange(name, e.target.value)}
      className="form-input disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
    >
      {options.map((opt) => (
        <option key={opt} value={opt}>{opt}</option>
      ))}
    </select>
  )
}

function ToggleControl({ name, label, checked, onChange }) {
  return (
    <div>
      <span className="form-label">{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-10 w-full items-center rounded-lg border px-3 text-sm font-medium transition ${
          checked
            ? 'border-brand-500 bg-brand-50 text-brand-700'
            : 'border-slate-300 bg-white text-slate-500'
        }`}
      >
        <span className={`mr-2 inline-block h-4 w-4 rounded-full ${checked ? 'bg-brand-600' : 'bg-slate-300'}`} />
        {checked ? 'Yes' : 'No'}
      </button>
    </div>
  )
}
