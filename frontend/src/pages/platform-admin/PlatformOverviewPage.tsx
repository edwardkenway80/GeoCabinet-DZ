import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'
import type { PlatformStats } from '../../types/platform'
import { Building2, Users, Shield, BarChart3 } from 'lucide-react'

interface StatCard {
  label: string
  value: string | number
  icon: React.ReactNode
  color: string
}

export default function PlatformOverviewPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    api.get<PlatformStats>('/api/v1/platform/stats/')
      .then((data) => {
        if (!cancelled) setStats(data)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'تعذر جلب الإحصائيات')
          // Show empty state rather than crashing — data source unavailable
          setStats(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const isPlatformAdmin = user?.is_platform_admin ?? false

  const statCards: StatCard[] = [
    { label: 'إجمالي المكاتب', value: loading ? '…' : stats?.total_tenants ?? '—', icon: <Building2 size={22} />, color: '#0f1f33' },
    { label: 'المكاتب النشطة', value: loading ? '…' : stats?.active_tenants ?? '—', icon: <Building2 size={22} />, color: '#2e7d32' },
    { label: 'المستخدمون الإجمالي', value: loading ? '…' : stats?.total_users ?? '—', icon: <Users size={22} />, color: '#1e3a5f' },
    { label: 'مسيرو المنصة', value: loading ? '…' : stats?.platform_admins ?? '—', icon: <Shield size={22} />, color: '#0284c7' },
  ]

  return (
    <div>
      <div style={S.header}>
        <h1 style={S.title}>نظرة عامة على المنصة</h1>
        <p style={S.sub}>
          مركز التحكم والإدارة لمراقبة جميع مكاتب GeoCabinet-DZ — {user?.full_name}
        </p>
        {!isPlatformAdmin && (
          <div style={S.warningBanner}>
            ⚠️ هذه الصفحة مخصصة لمسيري المنصة فقط.
          </div>
        )}
      </div>

      {error && <div style={S.err}>{error}</div>}

      <div style={S.grid}>
        {statCards.map(s => (
          <div key={s.label} style={S.card}>
            <div style={{ ...S.iconBox, background: s.color + '15', color: s.color }}>{s.icon}</div>
            <div>
              <div style={S.statVal}>{s.value}</div>
              <div style={S.statLabel}>{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={S.banner}>
        <BarChart3 size={18} color="#0284c7" />
        <span>
          البيانات المعروضة مستمدة من واجهات برمجية حقيقية ({loading ? 'جاري التحميل…' : 'متاحة'}).
          الوحدات الفرعية (المستخدمون، الإشعارات، الدعم، إلخ) قيد التطوير في المراحل اللاحقة.
        </span>
      </div>
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
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
    gap: 16, marginBottom: 24,
  },
  card: {
    background: '#fff', borderRadius: 12, padding: '20px 24px',
    display: 'flex', alignItems: 'center', gap: 16,
    boxShadow: '0 1px 3px rgba(0,0,0,.07)', border: '1px solid #e2e8f0',
  },
  iconBox: {
    width: 48, height: 48, borderRadius: 10, display: 'flex',
    alignItems: 'center', justifyContent: 'center', flexShrink: 0,
  },
  statVal: { fontSize: 26, fontWeight: 700, color: '#1a202c', lineHeight: 1 },
  statLabel: { fontSize: 12, color: '#64748b', marginTop: 4 },
  banner: {
    background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 10,
    padding: '12px 16px', display: 'flex', alignItems: 'flex-start', gap: 10,
    fontSize: 13, color: '#1e40af',
  },
  err: {
    background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626',
    padding: '12px 16px', borderRadius: 8, fontSize: 13,
  },
}