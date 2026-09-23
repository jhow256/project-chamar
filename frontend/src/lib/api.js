import axios from 'axios'

export const API_URL = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/$/, '')
let accessToken = sessionStorage.getItem('chamar.access') || ''
export const tokenStore = { get: () => accessToken, set: (value) => { accessToken = value || ''; value ? sessionStorage.setItem('chamar.access', value) : sessionStorage.removeItem('chamar.access') } }

function normalizeRecord(value) {
  if (Array.isArray(value)) return value.map(normalizeRecord)
  if (!value || typeof value !== 'object' || value instanceof Blob) return value
  const item = Object.fromEntries(Object.entries(value).map(([key, entry]) => [key, normalizeRecord(entry)]))
  const alias = (target, source) => { if (item[target] === undefined && item[source] !== undefined) item[target] = item[source] }
  ;[['nome','name'],['perfil','role'],['ativo','active'],['ativo','is_active'],['numero','number'],['titulo','title'],['descricao','description'],['prioridade','priority'],['solucao','solution'],['avaliacao','rating'],['criado_em','created_at'],['atualizado_em','updated_at'],['resolvido_em','resolved_at'],['texto','text'],['arquivo','download_url'],['status_anterior','previous_status'],['status_novo','new_status'],['alterado_por','changed_by_name']].forEach(([target, source]) => alias(target, source))
  if (item.sector_name !== undefined) item.setor = { id: item.sector, nome: item.sector_name }
  if (item.category_name !== undefined) item.categoria = { id: item.category, nome: item.category_name }
  if (item.requester_name !== undefined) item.solicitante = item.requester_name
  if (item.technician_name !== undefined) item.tecnico = item.technician_name
  if (item.author_name !== undefined) item.autor = item.author_name
  if (item.original_name !== undefined) item.nome = item.original_name
  return item
}

export const api = axios.create({ baseURL: API_URL, withCredentials: true, xsrfCookieName: 'csrftoken', xsrfHeaderName: 'X-CSRFToken', headers: { Accept: 'application/json' } })
api.interceptors.request.use((config) => { if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`; return config })
let refreshPromise = null
const isAuthRequest = (url = '') => /auth\/(login|refresh|logout)/.test(url)
api.interceptors.response.use((response) => { response.data = normalizeRecord(response.data); return response }, async (error) => {
  const original = error.config
  if (error.response?.status !== 401 || original?._retry || isAuthRequest(original?.url)) return Promise.reject(error)
  original._retry = true
  if (!refreshPromise) refreshPromise = axios.post(`${API_URL}/auth/refresh/`, {}, { withCredentials: true, xsrfCookieName: 'csrftoken', xsrfHeaderName: 'X-CSRFToken' }).then(({ data }) => { const token = data.access || data.access_token || data.token; if (!token) throw new Error('Token de acesso não retornado'); tokenStore.set(token); return token }).finally(() => { refreshPromise = null })
  try { const token = await refreshPromise; original.headers.Authorization = `Bearer ${token}`; return api(original) } catch (refreshError) { tokenStore.set(''); window.dispatchEvent(new Event('auth:expired')); return Promise.reject(refreshError) }
})
export const rowsOf = (data) => Array.isArray(data) ? data : (data?.results || data?.items || data?.data || [])
export const countOf = (data) => data?.count ?? rowsOf(data).length
export const idOf = (value) => value && typeof value === 'object' ? value.id : value
export const textOf = (value, fallback = '—') => value && typeof value === 'object' ? (value.nome || value.name || value.email || fallback) : (value ?? fallback)
export const messageOf = (error) => { const data = error?.response?.data; const fields = data && typeof data === 'object' ? Object.values(data).flat().find((value) => typeof value === 'string') : null; return data?.erro?.mensagem || data?.detail || data?.message || fields || (typeof data === 'string' ? data : null) || (error?.response?.status === 403 ? 'Você não tem permissão para realizar esta ação.' : error?.response?.status === 404 ? 'Recurso não encontrado.' : 'Não foi possível concluir a operação. Tente novamente.') }
export const downloadResponse = (data, filename) => { const url = URL.createObjectURL(new Blob([data])); const link = document.createElement('a'); link.href = url; link.download = filename; link.click(); URL.revokeObjectURL(url) }
