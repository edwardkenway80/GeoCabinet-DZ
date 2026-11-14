import { useEffect, useState } from 'react'
import { Users, FolderOpen, Briefcase, ClipboardList, TrendingUp } from 'lucide-react'
import { api } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import type { Membership } from '../types'

interface StatCard { label: string; value: string | number; icon: React.ReactNode; color: string }

export default function Dashboard() {
  const { activeTenant } = useAuth()
  const [members, setMembers] = useState<Membership[]>([])
  const [loadingMembers, setLoadingMembers] = useState(true)

  useEffect(() => {
    if (!activeTenant) return
    api.get<Membership[]>(`/api/v1/tenants/${activeTenant.id}/members/`)
      .then(setMembers)
      .catch(() => setMembers([]))
      .finally(() => setLoadingMembers(false))
  }, [activeTenant])

  const stats: StatCard[] = [
    { label: 'Membres de l\'équipe', value: loadingMembers ? '…' : members.length, icon: <Users size={22} />, color: '#1e3a5f' },
    { label: 'Dossiers', value: 'N/D', icon: <FolderOpen size={22} />, color: '#2e7d32' },
    { label: 'Projets actifs', value: 'N/D', icon: <Briefcase size={22} />, color: '#d97706' },
    { label: 'Missions en cours', value: 'N/D', icon: <ClipboardList size={22} />, color: '#0284c7' },
  ]

  return (
    <div>
      <div style={S.header}>
        <h1 style={S.title}>Tableau de bord</h1>
        <p style={S.sub}>Bienvenue dans votre espace de travail — <strong>{activeTenant?.name}</strong></p>
      </div>

      {/* Stat cards */}
      <div style={S.grid}>
        {stats.map(s => (
          <div key={s.label} style={S.card}>
            <div style={{ ...S.iconBox, background: s.color + '15', color: s.color }}>{s.icon}</div>
            <div>
              <div style={S.statVal}>{s.value}</div>
              <div style={S.statLabel}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Info banner */}
      <div style={S.banner}>
        <TrendingUp size={18} color="#0284c7" />
        <span>Les modules <strong>Dossiers, Projets, Missions, Clients</strong> sont en cours de développement. Les données affichées seront réelles dès que les APIs correspondantes seront disponibles.</span>
      </div>

      {/* Team preview */}
      {!loadingMembers && members.length > 0 && (
        <div style={S.section}>
          <h2 style={S.sectionTitle}>Équipe ({members.length} membres)</h2>
          <div style={S.table}>
            <div style={S.thead}>
              <span>Email</span><span>Rôle</span><span>Statut</span>
            </div>
            {members.map(m => (
              <div key={m.id} style={S.trow}>
                <span style={S.email}>{m.user_email}</span>
                <span style={S.role}>{ROLE_LABELS[m.role_code] ?? m.role_code}</span>
                <span style={{ ...S.badge, background: m.is_active ? '#e8f5e9' : '#fef2f2', color: m.is_active ? '#2e7d32' : '#dc2626' }}>
                  {m.is_active ? 'Actif' : 'Inactif'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const ROLE_LABELS: Record<string, string> = {
  owner: 'Propriétaire', expert_director: 'Directeur expert',
  project_manager: 'Chef de projet', surveyor: 'Géomètre',
  cad_gis_technician: 'Technicien CAD/SIG', secretary: 'Secrétaire',
  accountant: 'Comptable', viewer: 'Observateur',
}

const S: Record<string, React.CSSProperties> = {
  header: { marginBottom: 28 },
  title: { fontSize: 22, fontWeight: 700, color: '#1a202c', marginBottom: 4 },
  sub: { fontSize: 14, color: '#64748b' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 16, marginBottom: 24 },
  card: { background: '#fff', borderRadius: 12, padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 16, boxShadow: '0 1px 3px rgba(0,0,0,.07)', border: '1px solid #e2e8f0' },
  iconBox: { width: 48, height: 48, borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 },
  statVal: { fontSize: 26, fontWeight: 700, color: '#1a202c', lineHeight: 1 },
  statLabel: { fontSize: 12, color: '#64748b', marginTop: 4 },
  banner: { background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 10, padding: '12px 16px', display: 'flex', alignItems: 'flex-start', gap: 10, fontSize: 13, color: '#1e40af', marginBottom: 28 },
  section: { background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' },
  sectionTitle: { fontSize: 15, fontWeight: 600, color: '#1a202c', padding: '16px 20px', borderBottom: '1px solid #e2e8f0' },
  table: { display: 'flex', flexDirection: 'column' },
  thead: { display: 'grid', gridTemplateColumns: '1fr 180px 100px', padding: '10px 20px', background: '#f8fafc', fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' },
  trow: { display: 'grid', gridTemplateColumns: '1fr 180px 100px', padding: '12px 20px', borderTop: '1px solid #f1f5f9', alignItems: 'center' },
  email: { fontSize: 13, color: '#374151' },
  role: { fontSize: 13, color: '#64748b' },
  badge: { fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20, width: 'fit-content' },
}
