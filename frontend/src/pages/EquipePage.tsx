import { useEffect, useState } from 'react'
import { UserPlus } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import type { Membership } from '../types'

const ROLE_LABELS: Record<string, string> = {
  owner: 'Propriétaire', expert_director: 'Directeur expert',
  project_manager: 'Chef de projet', surveyor: 'Géomètre',
  cad_gis_technician: 'Technicien CAD/SIG', secretary: 'Secrétaire',
  accountant: 'Comptable', viewer: 'Observateur',
}

export default function EquipePage() {
  const { activeTenant } = useAuth()
  const [members, setMembers] = useState<Membership[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!activeTenant) return
    api.get<Membership[]>(`/api/v1/tenants/${activeTenant.id}/members/`)
      .then(setMembers)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [activeTenant])

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.title}>Équipe</h1>
          <p style={S.sub}>Membres du bureau <strong>{activeTenant?.name}</strong></p>
        </div>
        <button style={S.btn} disabled title="Fonctionnalité à venir">
          <UserPlus size={15} /> Ajouter un membre
        </button>
      </div>

      {loading && <div style={S.state}>Chargement…</div>}
      {error && <div style={S.err}>{error}</div>}

      {!loading && !error && (
        <div style={S.card}>
          <div style={S.thead}>
            <span>Membre</span><span>Rôle</span><span>Rejoint le</span><span>Statut</span>
          </div>
          {members.length === 0 && <div style={S.empty}>Aucun membre trouvé.</div>}
          {members.map(m => (
            <div key={m.id} style={S.row}>
              <div style={S.memberCell}>
                <div style={S.avatar}>{m.user_email.charAt(0).toUpperCase()}</div>
                <span style={S.email}>{m.user_email}</span>
              </div>
              <span style={S.role}>{ROLE_LABELS[m.role_code] ?? m.role_code}</span>
              <span style={S.date}>{new Date(m.joined_at).toLocaleDateString('fr-FR')}</span>
              <span style={{ ...S.badge, background: m.is_active ? '#e8f5e9' : '#fef2f2', color: m.is_active ? '#2e7d32' : '#dc2626' }}>
                {m.is_active ? 'Actif' : 'Inactif'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const S: Record<string, React.CSSProperties> = {
  header: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 },
  title: { fontSize: 22, fontWeight: 700, color: '#1a202c', marginBottom: 4 },
  sub: { fontSize: 14, color: '#64748b' },
  btn: { display: 'flex', alignItems: 'center', gap: 6, padding: '9px 16px', background: '#1e3a5f', color: '#fff', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'not-allowed', opacity: 0.6 },
  card: { background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' },
  thead: { display: 'grid', gridTemplateColumns: '1fr 200px 140px 100px', padding: '10px 20px', background: '#f8fafc', fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' },
  row: { display: 'grid', gridTemplateColumns: '1fr 200px 140px 100px', padding: '14px 20px', borderTop: '1px solid #f1f5f9', alignItems: 'center' },
  memberCell: { display: 'flex', alignItems: 'center', gap: 10 },
  avatar: { width: 32, height: 32, borderRadius: '50%', background: '#e8f0fb', color: '#1e3a5f', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700, flexShrink: 0 },
  email: { fontSize: 13, color: '#374151' },
  role: { fontSize: 13, color: '#64748b' },
  date: { fontSize: 13, color: '#64748b' },
  badge: { fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20, width: 'fit-content' },
  state: { color: '#64748b', fontSize: 14, padding: 20 },
  err: { background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '12px 16px', borderRadius: 8, fontSize: 13 },
  empty: { padding: '32px 20px', color: '#94a3b8', fontSize: 14, textAlign: 'center' },
}
