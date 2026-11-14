import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Building2 } from 'lucide-react'
import type { Tenant } from '../types'

export default function SelectOfficePage() {
  const { tenants, selectTenant, user, logout } = useAuth()
  const navigate = useNavigate()

  function handleSelect(t: Tenant) {
    selectTenant(t)
    navigate('/dashboard')
  }

  const statusLabel: Record<string, string> = {
    active: 'Actif', trial: 'Essai', suspended: 'Suspendu', closed: 'Fermé',
  }
  const statusColor: Record<string, string> = {
    active: '#2e7d32', trial: '#d97706', suspended: '#dc2626', closed: '#64748b',
  }

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div style={styles.header}>
          <div style={styles.logo}>
            <svg width="36" height="36" viewBox="0 0 40 40" fill="none">
              <rect width="40" height="40" rx="10" fill="#1e3a5f"/>
              <path d="M8 28L20 10L32 28H8Z" fill="white" opacity="0.9"/>
              <circle cx="20" cy="22" r="4" fill="#2e7d32"/>
            </svg>
            <span style={styles.logoText}>GeoCabinet DZ</span>
          </div>
          <p style={styles.welcome}>Bonjour, <strong>{user?.full_name}</strong></p>
          <h1 style={styles.title}>Choisissez votre bureau</h1>
          <p style={styles.subtitle}>Vous êtes membre de {tenants.length} bureaux</p>
        </div>

        <div style={styles.grid}>
          {tenants.map(t => (
            <button key={t.id} onClick={() => handleSelect(t)} style={styles.card}>
              <div style={styles.cardIcon}>
                <Building2 size={28} color="#1e3a5f" />
              </div>
              <div style={styles.cardBody}>
                <div style={styles.cardName}>{t.name}</div>
                <div style={styles.cardSlug}>/{t.slug}</div>
              </div>
              <span style={{ ...styles.badge, background: statusColor[t.status] + '20', color: statusColor[t.status] }}>
                {statusLabel[t.status] ?? t.status}
              </span>
            </button>
          ))}
        </div>

        <button onClick={logout} style={styles.logoutBtn}>Se déconnecter</button>
      </div>
    </div>
  )
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #1e3a5f 0%, #2d5a8e 100%)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '24px',
  },
  container: {
    background: '#fff', borderRadius: '16px', padding: '48px 40px',
    width: '100%', maxWidth: '560px', boxShadow: '0 20px 60px rgba(0,0,0,0.2)',
  },
  header: { marginBottom: '32px' },
  logo: { display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' },
  logoText: { fontSize: '18px', fontWeight: 700, color: '#1e3a5f' },
  welcome: { fontSize: '14px', color: '#64748b', marginBottom: '8px' },
  title: { fontSize: '22px', fontWeight: 700, color: '#1a202c', marginBottom: '4px' },
  subtitle: { fontSize: '14px', color: '#64748b' },
  grid: { display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' },
  card: {
    display: 'flex', alignItems: 'center', gap: '16px',
    padding: '16px 20px', border: '1.5px solid #e2e8f0', borderRadius: '10px',
    background: '#f8fafc', cursor: 'pointer', textAlign: 'left',
    transition: 'border-color 0.2s, box-shadow 0.2s',
  },
  cardIcon: {
    width: '48px', height: '48px', borderRadius: '10px',
    background: '#e8f0fb', display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
  },
  cardBody: { flex: 1 },
  cardName: { fontSize: '15px', fontWeight: 600, color: '#1a202c' },
  cardSlug: { fontSize: '12px', color: '#64748b', marginTop: '2px' },
  badge: {
    fontSize: '11px', fontWeight: 600, padding: '3px 10px',
    borderRadius: '20px', flexShrink: 0,
  },
  logoutBtn: {
    background: 'none', border: 'none', color: '#64748b',
    fontSize: '13px', cursor: 'pointer', textDecoration: 'underline',
    display: 'block', margin: '0 auto',
  },
}
