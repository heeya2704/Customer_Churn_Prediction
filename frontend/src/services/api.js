import axios from 'axios'

// Centralized API client.
//
// The app calls the API using RELATIVE paths (e.g. "/api/predict"):
//   - In production on Vercel, the API lives on the same domain under /api/*.
//   - In local development, the Vite dev server proxies /api -> the FastAPI
//     server (see vite.config.js), so the same relative paths work.
//
// VITE_API_URL is optional and only needed to point the frontend at a backend
// on a different origin (left empty for the standard single-domain setup).
const baseURL = import.meta.env.VITE_API_URL || ''

const client = axios.create({
  baseURL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

/**
 * Normalize backend/network errors into a consistent shape the UI can render.
 */
function toApiError(error) {
  if (error.response) {
    const { status, data } = error.response
    if (status === 422 && Array.isArray(data?.errors)) {
      return { status, message: 'Please correct the highlighted fields.', fieldErrors: data.errors }
    }
    return { status, message: data?.detail || 'The server rejected the request.', fieldErrors: [] }
  }
  // No response -> network / server unreachable.
  return {
    status: 0,
    message: 'Unable to reach the prediction service. Please try again.',
    fieldErrors: [],
  }
}

export const api = {
  async health() {
    const { data } = await client.get('/api/health')
    return data
  },
  async modelInfo() {
    const { data } = await client.get('/api/model-info')
    return data
  },
  async datasetStats() {
    const { data } = await client.get('/api/dataset/stats')
    return data
  },
  async predict(customer) {
    try {
      const { data } = await client.post('/api/predict', customer)
      return data
    } catch (error) {
      throw toApiError(error)
    }
  },
  async predictBatch(customers) {
    try {
      const { data } = await client.post('/api/predict/batch', { customers })
      return data
    } catch (error) {
      throw toApiError(error)
    }
  },
}

export { baseURL }
