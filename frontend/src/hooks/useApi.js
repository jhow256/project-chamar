import { useCallback, useEffect, useState } from 'react'
import { api, messageOf } from '../lib/api'
export function useApi(path, options = {}) {
  const [data, setData] = useState(null), [loading, setLoading] = useState(Boolean(path)), [error, setError] = useState('')
  const load = useCallback(async () => { if (!path) return; setLoading(true); setError(''); try { const response = await api.get(path, { params: options.params }); setData(response.data); return response.data } catch (err) { setError(messageOf(err)); throw err } finally { setLoading(false) } }, [path, JSON.stringify(options.params || {})])
  useEffect(() => { load().catch(() => {}) }, [load])
  return { data, loading, error, reload: load, setData }
}
