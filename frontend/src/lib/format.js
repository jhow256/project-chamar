export const STATUS = { ABERTO: 'Aberto', EM_ATENDIMENTO: 'Em atendimento', AGUARDANDO_USUARIO: 'Aguardando usuário', RESOLVIDO: 'Resolvido', FECHADO: 'Fechado', CANCELADO: 'Cancelado' }
export const PRIORITY = { BAIXA: 'Baixa', MEDIA: 'Média', ALTA: 'Alta', CRITICA: 'Crítica' }
export const dateTime = (value) => value ? new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : '—'
export const dateOnly = (value) => value ? new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short' }).format(new Date(value)) : '—'
export const statusLabel = (value) => STATUS[value] || value || '—'
export const priorityLabel = (value) => PRIORITY[value] || value || '—'
export const roleOf = (user) => String(user?.perfil || user?.role || user?.tipo || '').toUpperCase()
export const isStaff = (user) => Boolean(user?.is_staff || user?.is_superuser || roleOf(user) === 'ADMIN' || roleOf(user) === 'ADMINISTRADOR')
export const isTech = (user) => isStaff(user) || ['TECNICO', 'TÉCNICO', 'TECHNICIAN'].includes(roleOf(user))
export const initials = (name = 'U') => name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase()
