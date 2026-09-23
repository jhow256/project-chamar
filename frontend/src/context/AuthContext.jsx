import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import { api, tokenStore } from '../lib/api'

export const AuthContext = createContext(null)
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null), [loading, setLoading] = useState(true)
  const loadMe = useCallback(async () => {
    const { data: profile } = await api.get('/auth/me/')
    let userData = profile
    try {
      const { data: administrativeProfile } = await api.get(`/users/${profile.id}/`)
      userData = { ...profile, ...administrativeProfile }
    } catch (error) {
      if (![403, 404].includes(error.response?.status)) throw error
    }
    setUser(userData)
    return userData
  }, [])
  const clear = useCallback(() => { tokenStore.set(''); setUser(null) }, [])
  useEffect(() => { let active = true; const boot = async () => { try { if (!tokenStore.get()) { const { data } = await api.post('/auth/refresh/'); tokenStore.set(data.access || data.access_token || data.token) } await loadMe() } catch { if (active) clear() } finally { if (active) setLoading(false) } }; boot(); const expired = () => clear(); window.addEventListener('auth:expired', expired); return () => { active = false; window.removeEventListener('auth:expired', expired) } }, [clear, loadMe])
  const login = async (email, senha) => { const { data } = await api.post('/auth/login/', { email, password: senha }); const token = data.access || data.access_token || data.token; if (!token) throw new Error('Credenciais aceitas, mas a API não retornou o token.'); tokenStore.set(token); return loadMe() }
  const logout = async () => { try { await api.post('/auth/logout/') } finally { clear() } }
  const value = useMemo(() => ({ user, loading, login, logout, reloadUser: loadMe, setUser }), [user, loading, loadMe])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
