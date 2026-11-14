import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'
import type { PlatformUser, PlatformMembership } from '../../types/platform'
import { Building2 } from 'lucide-react'

const ROLE_LABELS: Record<string, string> = {
  owner: 'Propriétaire', expert_director: 'Directeur expert',
  project_manager: 'Chef de projet', surveyor: 'Géomètre',
  cad_gis_technician: 'Technicien CAD/SIG', secretary: 'Secrétaire',
  accountant: 'Comptable', viewer: 'Observateur',
}

export default function PlatformUserDetailsPage() {
  const { userId } = useParams<{ userId: string }>()
  const { user } = useAuth()
  const [userData, setUserData] = useState<PlatformUser | null>(null)
  const [memberships, setMemberships] = useState<PlatformMembership[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const isPlatformAdmin = user?.is_platform_admin ?? false

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    setError('')
    Promise.all([
      api.get<PlatformUser>(`/api/v1/platform/users/${userId}/`),
      api.get<PlatformMembership[]>(`/api/v1/platform/users/${userId}/memberships/`),
    ])
      .then(([userRes, membershipsRes]) => {
        setUserData(userRes)
        setMemberships(membershipsRes)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'تعذر جلب تفاصيل المستخدم')
      })
      .finally(() => setLoading(false))
  }, [userId])

  return (
    <div>
      <div style={S.header}>
        <h1 style={S.title}>تفاصيل المستخدم</h1>
        <p style={S.sub}>مراجعة الحساب، الصلاحيات، والعضويات في المكاتب</p>
      </div>

      {!isPlatformAdmin && (
        <div style={S.warningBanner}>
          ⚠️ هذه الصفحة مخصصة لمسيري المنصة فقط.
        </div>
      )}

      {error && <div style={S.err}>{error}</div>}

      {loading && <div style={S.state}>جاري تحميل البيانات…</div>}

      {!loading && !error && userData && (
        <div>
          <div style={S.userCard}>
            <div style={S.avatar}>{userData.full_name.charAt(0).toUpperCase() ?? '?'}</div>
            <div style={S.userInfo}>
              <h2 style={S.userName}>{userData.full_name}</h2>
              <span style={S.userEmail}>{userData.email}</span>
              <div style={S.badges}>
                <span style={{ ...S.badge, background: userData.is_platform_admin ? '#e8f5e9' : '#f1f5f9', color: userData.is_platform_admin ? '#2e7d32' : '#64748b' }}>
                  {userData.is_platform_admin ? 'مسير المنصة' : 'مستخدم'}
                </span>
                <span style={{ ...S.badge, background: userData.is_active ? '#e8f5e9' : '#fef2f2', color: userData.is_active ? '#2e7d32' : '#dc2626' }}>
                  {userData.is_active ? 'Actif' : 'Inactif'}
                </span>
              </div>
              <p style={S.locale}>اللغة المفضلة: {userData.preferred_locale}</p>
              <p style={S.createdAt}>تاريخ الإنشاء: {new Date(userData.created_at).toLocaleDateString('fr-FR')}</p>
            </div>
          </div>

          <div style={S.section}>
            <h3 style={S.sectionTitle}>
              <Building2 size={16} style={{ marginRight: 6 }} /> العضويات ({memberships.length})
            </h3>
            {memberships.length === 0 && (
              <div style={S.empty}>لا يوجد 소속 لهذا المستخدم في أي مكتب.</div>
            )}
            {memberships.map(m => (
              <div key={m.id} style={S.membershipRow}>
                <div style={S.tenantInfo}>
                  <span style={S.tenantName}>{m.tenant_name}</span>
                  <span style={S.tenantSlug}>/{m.tenant_slug}</span>
                </div>
                <span style={S.roleLabel}>{ROLE_LABELS[m.role_code] ?? m.role_code}</span>
                <span style={{ ...S.statusChip, background: m.is_active ? '#e8f5e9' : '#fef2f2', color: m.is_active ? '#2e7d32' : '#dc2626' }}>
                  {m.is_active ? 'نشط' : 'غير نشط'}
                </span>
                <span style={S.joinedAt}>{new Date(m.joined_at).toLocaleDateString('fr-FR')}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const S: Record<string, React.CSSProperties> = {
  header: { marginBottom: 28 },
  title: { fontSize: 22, fontWeight: 700, color: '#1a202c', marginBottom: 4 },
  sub: { fontSize: 14, color: '#64748b' },
  warningBanner: {
    background: '#fef3c7', border: '1px solid #fcd34d', borderRadius: 8,
    padding: '10px 16px', fontSize: 13, color: '#92400e', marginBottom: 20,
  },
  err: {
    background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626',
    padding: '12px 16px', borderRadius: 8, fontSize: 13, marginBottom: 20,
  },
  state: { color: '#64748b', fontSize: 14, padding: 20 },
  userCard: {
    background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
    padding: '24px 32px', display: 'flex', alignItems: 'center', gap: 20,
    marginBottom: 24,
  },
  avatar: {
    width: 48, height: 48, borderRadius: '50%', background: '#e8f0fb',
    color: '#1e3a5f', display: 'flex', alignItems: 'center',
    justifyContent: 'center', fontSize: 20, fontWeight: 700, flexShrink: 0,
  },
  userInfo: { flex: 1, display: 'flex', flexDirection: 'column', gap: 8 },
  userName: { fontSize: 18, fontWeight: 700, color: '#1a202c', margin: 0 },
  userEmail: { fontSize: 14, color: '#64748b', margin: 0 },
  badges: { display: 'flex', gap: 8, marginTop: 8 },
  badge: {
    fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20,
    width: 'fit-content',
  },
  locale: { fontSize: 13, color: '#374151', margin: 0 },
  createdAt: { fontSize: 13, color: '#64748b', margin: 0 },
  section: { background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' },
  sectionTitle: {
    fontSize: 15, fontWeight: 600, color: '#1a202c', padding: '16px 20px',
    borderBottom: '1px solid #e2e8f0', margin: 0, display: 'flex', alignItems: 'center',
  },
  empty: { padding: '32px 20px', color: '#94a3b8', fontSize: 14, textAlign: 'center' },
  membershipRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 160px 120px 160px',
    padding: '12px 20px',
    borderTop: '1px solid #f1f5f9',
    alignItems: 'center',
  },
  tenantInfo: { display: 'flex', flexDirection: 'column', gap: 2 },
  tenantName: { fontSize: 13, fontWeight: 600, color: '#1a202c' },
  tenantSlug: { fontSize: 12, color: '#64748b', fontFamily: 'monospace' },
  roleLabel: { fontSize: 13, color: '#64748b' },
  statusChip: {
    fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20,
    width: 'fit-content',
  },
  joinedAt: { fontSize: 13, color: '#64748b' },
}