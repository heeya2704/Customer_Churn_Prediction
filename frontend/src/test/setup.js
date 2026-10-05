import '@testing-library/jest-dom'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// Recharts' ResponsiveContainer needs a non-zero size; jsdom reports 0.
// Stub the observer so charts render in tests without warnings.
globalThis.ResizeObserver =
  globalThis.ResizeObserver ||
  class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})
