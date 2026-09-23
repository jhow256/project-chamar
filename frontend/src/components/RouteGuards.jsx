import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { isStaff, isTech } from '../lib/format'
import { Spinner } from './Ui'
export function PrivateRoute() { const { user, loading } = useAuth(), location = useLocation(); if (loading) return <main className="center-page"><Spinner label="Verificando sessão" /></main>; return user ? <Outlet /> : <Navigate to="/login" state={{ from: location }} replace /> }
export function PublicOnlyRoute() { const { user, loading } = useAuth(); if (loading) return <main className="center-page"><Spinner /> </main>; return user ? <Navigate to="/chamados" replace /> : <Outlet /> }
export function RoleRoute({ role }) { const { user } = useAuth(); const allowed = role === 'staff' ? isStaff(user) : isTech(user); return allowed ? <Outlet /> : <Navigate to="/403" replace /> }
