import { Component } from 'react'
export class ErrorBoundary extends Component {
  state = { error: null }
  static getDerivedStateFromError(error) { return { error } }
  componentDidCatch(error, info) { console.error('Erro não tratado na interface', error, info) }
  render() { if (this.state.error) return <main className="fatal"><div><span className="brand-mark">C</span><h1>Algo não saiu como esperado</h1><p>A interface encontrou um erro inesperado. Seus dados não foram alterados.</p><button className="button" onClick={() => window.location.assign('/')}>Recarregar aplicação</button></div></main>; return this.props.children }
}
