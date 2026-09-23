import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError } from '../services/api'

/**
 * Fetch data from the backend with loading/error/empty states and a
 * manual reload function. Re-runs whenever `deps` changes.
 */
export function useApi(fetcher, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const requestId = useRef(0)

  const load = useCallback(() => {
    const id = ++requestId.current
    setLoading(true)
    setError(null)
    fetcher()
      .then((result) => {
        if (id !== requestId.current) return
        setData(result)
        setLoading(false)
      })
      .catch((err) => {
        if (id !== requestId.current) return
        setError(err instanceof ApiError ? err : new ApiError('Unexpected error', 0))
        setLoading(false)
      })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [load])

  return { data, loading, error, reload: load }
}

const HEALTH_POLL_INTERVAL_MS = 15000

/**
 * Poll GET /api/health at a reasonable interval and report API/database
 * status. Never polls faster than HEALTH_POLL_INTERVAL_MS, and pauses
 * while the tab is hidden. Shared by the sidebar and top bar so the
 * endpoint is only hit once per interval, not once per consumer.
 */
export function useHealthStatus(getHealth) {
  const [state, setState] = useState({ apiStatus: 'CHECKING', dbStatus: 'CHECKING' })

  useEffect(() => {
    let cancelled = false

    const check = async () => {
      try {
        const result = await getHealth()
        if (!cancelled) {
          setState({
            apiStatus: result?.status === 'healthy' ? 'ONLINE' : 'OFFLINE',
            dbStatus: result?.database === 'connected' ? 'CONNECTED' : 'UNAVAILABLE',
          })
        }
      } catch {
        if (!cancelled) setState({ apiStatus: 'OFFLINE', dbStatus: 'UNAVAILABLE' })
      }
    }

    check()
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') check()
    }, HEALTH_POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      clearInterval(interval)
    }
  }, [getHealth])

  return state
}
