import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { initials, isStaff, isTech } from '../lib/format'

const Icon = ({ children }) => <span className="nav-icon" aria-hidden="true">{children}</span>
export function AppShell() {
  const { user, logout } = useAuth(), navigate = useNavigate(), [open, setOpen] = useState(false)
  const name = user?.nome || user?.name || user?.first_name || user?.email || 'Usuário'
  const links = [
    { to: '/chamados', label: 'Chamados', icon: '▤' }, { to: '/chamados/novo', label: 'Novo chamado', icon: '+' },
    ...(isTech(user) ? [{ to: '/dashboard', label: 'Dashboard', icon: '⌁' }, { to: '/cadastros/setores', label: 'Setores', icon: '⌂' }, { to: '/cadastros/categorias', label: 'Categorias', icon: '◇' }, { to: '/cadastros/equipamentos', label: 'Equipamentos', icon: '▣' }] : []),
    ...(isStaff(user) ? [{ to: '/admin/usuarios', label: 'Usuários', icon: '♙' }] : []),
    { to: '/perfil', label: 'Meu perfil', icon: '○' },
  ]
  const signOut = async () => { await logout(); navigate('/login', { replace: true }) }
  return <div className="app-shell">
    <button className="mobile-menu" onClick={() => setOpen((value) => !value)} aria-label="Abrir menu" aria-expanded={open}>☰</button>
    {open && <button className="sidebar-overlay" aria-label="Fechar menu" onClick={() => setOpen(false)} />}
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <NavLink to="/chamados" className="brand" onClick={() => setOpen(false)}><span className="brand-mark">C</span><span><strong>Chamar</strong><small>Suporte de TI</small></span></NavLink>
      <nav aria-label="Navegação principal">{links.map((link) => <NavLink key={link.to} to={link.to} end={link.to === '/chamados'} onClick={() => setOpen(false)}><Icon>{link.icon}</Icon>{link.label}</NavLink>)}</nav>
      <div className="sidebar-profile"><span className="avatar">{initials(name)}</span><div><strong title={name}>{name}</strong><small>{isStaff(user) ? 'Administrador' : isTech(user) ? 'Técnico' : 'Colaborador'}</small></div><button onClick={signOut} aria-label="Sair" title="Sair">↪</button></div>
    </aside>
    <main id="conteudo" className="main-content"><Outlet /></main>
  </div>
}
