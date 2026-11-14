import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function LoginPage() {
  const { login, tenants, activeTenant } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      // AuthContext sets activeTenant if only one tenant
      // Navigation handled by App router after state update
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Erreur de connexion')
    } finally {
      setLoading(false)
    }
  }

  // After login, if single tenant → dashboard; else → tenant selector
  if (activeTenant) { navigate('/dashboard'); return null }
  if (tenants.length > 1) { navigate('/select-office'); return null }

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <div style={styles.logo}>
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <rect width="40" height="40" rx="10" fill="#1e3a5f"/>
            <path d="M8 28L20 10L32 28H8Z" fill="white" opacity="0.9"/>
            <circle cx="20" cy="22" r="4" fill="#2e7d32"/>
          </svg>
          <span style={styles.logoText}>GeoCabinet DZ</span>
        </div>

        <h1 style={styles.title}>Connexion</h1>
        <p style={styles.subtitle}>Accédez à votre espace de travail</p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.field}>
            <label style={styles.label}>Adresse e-mail</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="vous@cabinet.dz"
              required
              autoFocus
              style={styles.input}
            />
          </div>

          <div style={styles.field}>
            <label style={styles.label}>Mot de passe</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              style={styles.input}
            />
          </div>

          {error && <div style={styles.error}>{error}</div>}

          <button type="submit" disabled={loading} style={styles.btn}>
            {loading ? 'Connexion en cours…' : 'Se connecter'}
          </button>
        </form>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 100%)',
    padding: '24px',
  },
  card: {
    background: '#fff',
    borderRadius: '16px',
    padding: '48px 40px',
    width: '100%',
    maxWidth: '420px',
    boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
  },
  logo: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '32px',
  },
  logoText: {
    fontSize: '20px',
    fontWeight: 700,
    color: '#1e3a5f',
  },
  title: {
    fontSize: '24px',
    fontWeight: 700,
    color: '#1a202c',
    marginBottom: '8px',
  },
  subtitle: {
    fontSize: '14px',
    color: '#64748b',
    marginBottom: '32px',
  },
  form: { display: 'flex', flexDirection: 'column', gap: '20px' },
  field: { display: 'flex', flexDirection: 'column', gap: '6px' },
  label: { fontSize: '13px', fontWeight: 500, color: '#374151' },
  input: {
    padding: '10px 14px',
    border: '1.5px solid #e2e8f0',
    borderRadius: '8px',
    fontSize: '14px',
    transition: 'border-color 0.2s',
    background: '#f8fafc',
  },
  error: {
    background: '#fef2f2',
    border: '1px solid #fecaca',
    color: '#dc2626',
    padding: '10px 14px',
    borderRadius: '8px',
    fontSize: '13px',
  },
  btn: {
    background: '#1e3a5f',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    padding: '12px',
    fontSize: '15px',
    fontWeight: 600,
    cursor: 'pointer',
    transition: 'background 0.2s',
    marginTop: '4px',
  },
}
