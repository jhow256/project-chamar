import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { api, messageOf } from '../lib/api'
import { useAuth } from '../hooks/useAuth'
import { Alert } from '../components/Ui'

function AuthVisual() {
  return <section className="auth-visual" aria-label="Identidade institucional">
    <div className="institutional-identity">
      <header className="implurb-lockup">
        <strong>IMPLURB</strong>
        <span>Instituto Municipal de<br />Planejamento Urbano</span>
      </header>
      <img className="coat-of-arms" src="/Brasao.png" alt="Brasão da Prefeitura de Manaus" />
      <footer className="manaus-lockup">
        <span>Prefeitura de</span>
        <strong>Manaus</strong>
        <b>O trabalho não para!</b>
      </footer>
    </div>
  </section>
}
export function LoginPage() {
  const { login } = useAuth(), navigate = useNavigate(), location = useLocation()
  const [form, setForm] = useState({ email: '', senha: '' }), [show, setShow] = useState(false), [loading, setLoading] = useState(false), [error, setError] = useState('')
  const submit = async (event) => { event.preventDefault(); setLoading(true); setError(''); try { await login(form.email, form.senha); navigate(location.state?.from?.pathname || '/chamados', { replace: true }) } catch (err) { setError(messageOf(err)) } finally { setLoading(false) } }
  return <main className="auth-page"><AuthVisual /><section className="auth-form-pane"><div className="auth-card"><span className="eyebrow">Bem-vindo de volta</span><h2>Acesse sua conta</h2><p className="muted">Entre com suas credenciais institucionais.</p><Alert>{error}</Alert><form onSubmit={submit}><label>E-mail institucional<input type="email" autoComplete="username" placeholder="nome@empresa.com" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required autoFocus /></label><label>Senha<div className="password-field"><input type={show ? 'text' : 'password'} autoComplete="current-password" placeholder="Digite sua senha" value={form.senha} onChange={(e) => setForm({ ...form, senha: e.target.value })} required /><button type="button" onClick={() => setShow(!show)} aria-label={show ? 'Ocultar senha' : 'Mostrar senha'}>{show ? 'Ocultar' : 'Exibir'}</button></div></label><div className="form-meta"><label className="check"><input type="checkbox" /> Manter e-mail preenchido</label><Link to="/recuperar-senha">Esqueci minha senha</Link></div><button className="button wide" disabled={loading}>{loading ? 'Entrando...' : 'Entrar'}</button></form><p className="auth-footer">Ao entrar, você concorda com a <Link to="/privacidade">Política de Privacidade</Link>.</p></div></section></main>
}
export function PasswordResetPage() {
  const [email, setEmail] = useState(''), [loading, setLoading] = useState(false), [notice, setNotice] = useState(''), [error, setError] = useState('')
  const submit = async (event) => { event.preventDefault(); setLoading(true); setError(''); try { await api.post('/auth/password-reset/', { email }); setNotice('Se o e-mail estiver cadastrado, você receberá as instruções de recuperação.') } catch (err) { setError(messageOf(err)) } finally { setLoading(false) } }
  return <main className="simple-auth"><section><Link className="brand dark" to="/login"><span className="brand-mark">C</span><strong>Chamar</strong></Link><span className="eyebrow">Recuperação de acesso</span><h1>Redefina sua senha</h1><p>Informe seu e-mail institucional. Enviaremos as instruções com segurança.</p><Alert type="success">{notice}</Alert><Alert>{error}</Alert>{!notice && <form onSubmit={submit}><label>E-mail<input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus /></label><button className="button wide" disabled={loading}>{loading ? 'Enviando...' : 'Enviar instruções'}</button></form>}<Link className="back-link" to="/login">← Voltar para o login</Link></section></main>
}
