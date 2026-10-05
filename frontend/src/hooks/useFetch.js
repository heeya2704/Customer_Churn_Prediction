import { useCallback, useEffect, useState } from 'react'

/**
 * Minimal data-fetching hook with loading/error/refetch handling.
 * `fetcher` must be a stable function (wrap in useCallback by the caller).
 */
export default function useFetch(fetcher) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const run = useCallback(() => {
    let active = true
    setLoading(true)
    setError(null)
    fetcher()
      .then((result) => active && setData(result))
      .catch((err) => active && setError(err?.message || 'Something went wrong.'))
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [fetcher])

  useEffect(() => run(), [run])

  return { data, loading, error, refetch: run }
}
