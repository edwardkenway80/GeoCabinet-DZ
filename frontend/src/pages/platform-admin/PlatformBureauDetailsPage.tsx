import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'
import type { PlatformTenant, PlatformMembership } from '../../types/platform'
import { Building2, Users } from 'lucide-react'

const STATUS_LABEL: Record<string, string> = {
  active: 'نشط', trial: 'تجريبي', suspended: 'معلّق', closed: 'مغلق',
}
const STATUS_COLOR: Record<string, string> = {
  active: '#2e7d32', trial: '#d97706', suspended: '#dc2626', closed: '#64748b',
}

const ROLE_LABELS: Record<string, string> = {
  owner: 'Propriétaire', expert_director: 'Directeur expert',
  project_manager: 'Chef de projet', surveyor: 'Géomètre',
  cad_gis_technician: 'Technicien CAD/SIG', secretary: 'Secrétaire',
  accountant: 'Comptable', viewer: 'Observateur',
}

export default function PlatformBureauDetailsPage() {
  const { tenantId } = useParams<{ tenantId: string }>()
  const { user } = useAuth()
  const [tenant, setTenant] = useState<PlatformTenant | null>(null)
  const [members, setMembers] = useState<PlatformMembership[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const isPlatformAdmin = user?.is_platform_admin ?? false

  useEffect(() => {
    if (!tenantId) return
    setLoading(true)
    setError('')
    Promise.all([
      api.get<PlatformTenant>(`/api/v1/platform/tenants/${tenantId}/`),
      api.get<PlatformMembership[]>(`/api/v1/platform/tenants/${tenantId}/members/`),
    ])
      .then(([tenantRes, membersRes]) => {
        setTenant(tenantRes)
        setMembers(membersRes)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'تعذر جلب تفاصيل المكتب')
      })
      .finally(() => setLoading(false))
  }, [tenantId])

  return (
    <div>
      <div style={S.header}>
        <h1 style={S.title}>تفاصيل المكتب</h1>
        <p style={S.sub}>معلومات المكتب، الأعضاء، والصلاحيات</p>
      </div>

      {!isPlatformAdmin && (
        <div style={S.warningBanner}>
          ⚠️ هذه الصفحة مخصصة لمسيري المنصة فقط.
        </div>
      )}

      {error && <div style={S.err}>{error}</div>}

      {loading && <div style={S.state}>جاري تحميل البيانات…</div>}

      {!loading && !error && tenant && (
        <div>
          <div style={S.tenantCard}>
            <div style={S.iconWrap}>
              <Building2 size={24} style={{ color: '#fff' }} />
            </div>
            <div style={S.tenantInfo}>
              <h2 style={S.tenantName}>{tenant.name}</h2>
              <span style={S.tenantSlug}>/{tenant.slug}</span>
              <span style={{ ...S.statusChip, background: STATUS_COLOR[tenant.status] + '20', color: STATUS_COLOR[tenant.status] }}>
                {STATUS_LABEL[tenant.status] ?? tenant.status}
              </span>
              <p style={S.locale}>اللغة الافتراضية: {tenant.default_locale}</p>
              <p style={S.createdAt}>تاريخ الإنشاء: {new Date(tenant.created_at).toLocaleDateString('fr-FR')}</p>
              <p style={S.memberCount}>عدد الأعضاء النشطين: {tenant.member_count}</p>
            </div>
          </div>

          <div style={S.section}>
            <h3 style={S.sectionTitle}>
              <Users size={16} style={{ marginRight: 6 }} /> الأعضاء ({members.length})
            </h3>
            {members.length === 0 && (
              <div style={S.empty}>لا يوجد أعضاء في هذا المكتب.</div>
            )}
            {members.map(m => (
              <div key={m.id} style={S.memberRow}>
                <div style={S.memberInfo}>
                  <span style={S.memberName}>{m.user_full_name}</span>
                  <span style={S.memberEmail}>{m.user_email}</span>
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
  tenantCard: {
    background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0',
    padding: '24px 32px', display: 'flex', alignItems: 'center', gap: 24,
    marginBottom: 24,
  },
  iconWrap: {
    width: 48, height: 48, borderRadius: 10, background: '#e8f0fb',
    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
  },
  tenantInfo: { flex: 1, display: 'flex', flexDirection: 'column', gap: 6 },
  tenantName: { fontSize: 18, fontWeight: 700, color: '#1a202c', margin: 0 },
  tenantSlug: { fontSize: 14, color: '#64748b', fontFamily: 'monospace', margin: 0 },
  statusChip: {
    fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20,
    width: 'fit-content',
  },
  locale: { fontSize: 13, color: '#374151', margin: 0 },
  createdAt: { fontSize: 13, color: '#64748b', margin: 0 },
  memberCount: { fontSize: 13, color: '#374151', margin: 0 },
  section: { background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' },
  sectionTitle: {
    fontSize: 15, fontWeight: 600, color: '#1a202c', padding: '16px 20px',
    borderBottom: '1px solid #e2e8f0', margin: 0, display: 'flex', alignItems: 'center',
  },
  empty: { padding: '32px 20px', color: '#94a3b8', fontSize: 14, textAlign: 'center' },
  memberRow: {
    display: 'grid',
    gridTemplateColumns: '1fr 160px 120px 160px',
    padding: '12px 20px',
    borderTop: '1px solid #f1f5f9',
    alignItems: 'center',
  },
  memberInfo: { display: 'flex', flexDirection: 'column', gap: 2 },
  memberName: { fontSize: 13, fontWeight: 600, color: '#1a202c' },
  memberEmail: { fontSize: 12, color: '#64748b' },
  roleLabel: { fontSize: 13, color: '#64748b' },
  joinedAt: { fontSize: 13, color: '#64748b' },
}