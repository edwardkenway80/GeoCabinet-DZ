import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'
import type { PlatformTenant, PaginatedResponse } from '../../types/platform'

const STATUS_LABEL: Record<string, string> = {
  active: 'نشط', trial: 'تجريبي', suspended: 'معلّق', closed: 'مغلق',
}
const STATUS_COLOR: Record<string, string> = {
  active: '#2e7d32', trial: '#d97706', suspended: '#dc2626', closed: '#64748b',
}

export default function PlatformBureauxPage() {
  const { user } = useAuth()
  const [tenants, setTenants] = useState<PlatformTenant[]>([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    api.get<PaginatedResponse<PlatformTenant>>('/api/v1/platform/tenants/')
      .then((data) => {
        if (!cancelled) {
          setTenants(data.results)
          setCount(data.count ?? 0)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'تعذر جلب قائمة المكاتب')
          setTenants([])
          setCount(0)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const isPlatformAdmin = user?.is_platform_admin ?? false

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.title}>إدارة المكاتب</h1>
          <p style={S.sub}>قائمة جميع المكاتب المسجلة في منصة GeoCabinet-DZ</p>
        </div>
      </div>

      {!isPlatformAdmin && (
        <div style={S.warningBanner}>
          ⚠️ هذه الصفحة مخصصة لمسيري المنصة فقط.
        </div>
      )}

      {error && <div style={S.err}>{error}</div>}

      {loading && <div style={S.state}>جاري تحميل المكاتب…</div>}

      {!loading && !error && (
        <div style={S.card}>
          <div style={S.thead}>
            <span>المكتب</span><span>الرابط</span><span>الحالة</span>
            <span>الأعضاء</span><span>تاريخ الإنشاء</span>
          </div>
          {tenants.length === 0 && (
            <div style={S.empty}>لا توجد مكاتب مسجلة.</div>
          )}
          {tenants.map(t => (
            <div key={t.id} style={S.row}>
              <div style={S.tenantCell}>
                <Link to={`/platform-admin/bureaux/${t.id}`} style={S.tenantLink}>
                  <span style={S.tenantName}>{t.name}</span>
                </Link>
                <span style={S.tenantSlug}>/{t.slug}</span>
              </div>
              <span style={S.statusLabel}>{STATUS_LABEL[t.status] ?? t.status}</span>
              <span style={{ ...S.statusChip, background: STATUS_COLOR[t.status] + '20', color: STATUS_COLOR[t.status] }}>{STATUS_LABEL[t.status] ?? t.status}</span>
              <span style={S.memberCount}>{t.member_count}</span>
              <span style={S.createdAt}>{new Date(t.created_at).toLocaleDateString('fr-FR')}</span>
            </div>
          ))}
        </div>
      )}

      {!loading && !error && count > 0 && (
        <div style={S.pagination}>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page <= 1}
            style={page <= 1 ? S.paginationBtnDisabled : S.paginationBtn}
          >
            السابقة
          </button>
          <span style={S.paginationInfo}>
            الصفحة {page} من {Math.max(1, Math.ceil(count / 20))} (عرض {Math.min(page * 20, count)} من {count})
          </span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page * 20 >= count}
            style={page * 20 >= count ? S.paginationBtnDisabled : S.paginationBtn}
          >
            التالية
          </button>
        </div>
      )}
    </div>
  )
}

const S: Record<string, React.CSSProperties> = {
  header: { display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24 },
  title: { fontSize: 22, fontWeight: 700, color: '#1a202c', marginBottom: 4 },
  sub: { fontSize: 14, color: '#64748b' },
  warningBanner: { background: '#fef3c7', border: '1px solid #fcd34d', borderRadius: 8, padding: '10px 16px', fontSize: 13, color: '#92400e', marginBottom: 20 },
  err: { background: '#fef2f2', border: '1px solid #fecaca', color: '#dc2626', padding: '12px 16px', borderRadius: 8, fontSize: 13, marginBottom: 20 },
  state: { color: '#64748b', fontSize: 14, padding: 20 },
  card: { background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' },
  thead: { display: 'grid', gridTemplateColumns: '1fr 160px 120px 80px 160px', padding: '10px 20px', background: '#f8fafc', fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' },
  row: { display: 'grid', gridTemplateColumns: '1fr 160px 120px 80px 160px', padding: '12px 20px', borderTop: '1px solid #f1f5f9', alignItems: 'center' },
  tenantCell: { display: 'flex', flexDirection: 'column', gap: 2 },
  tenantLink: { color: '#1e3a5f', textDecoration: 'none', fontWeight: 600, fontSize: 13 },
  tenantName: { fontSize: 13, fontWeight: 600, color: '#1a202c' },
  tenantSlug: { fontSize: 12, color: '#64748b', fontFamily: 'monospace' },
  statusLabel: { fontSize: 13, color: '#64748b' },
  statusChip: { fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20, width: 'fit-content' },
  memberCount: { fontSize: 13, color: '#374151' },
  createdAt: { fontSize: 13, color: '#64748b' },
  empty: { padding: '32px 20px', color: '#94a3b8', fontSize: 14, textAlign: 'center' },
  pagination: { display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, marginTop: 20, paddingTop: 16, borderTop: '1px solid #e2e8f0' },
  paginationBtn: { padding: '6px 16px', border: '1px solid #e2e8f0', borderRadius: 6, background: '#fff', cursor: 'pointer', fontSize: 13, color: '#1e3a5f' },
  paginationBtnDisabled: { padding: '6px 16px', border: '1px solid #e2e8f0', borderRadius: 6, background: '#f1f5f9', cursor: 'not-allowed', fontSize: 13, color: '#cbd5e1' },
  paginationInfo: { fontSize: 12, color: '#64748b', fontWeight: 500 },
}
