import { useState, useEffect, useCallback } from 'react'
import { api } from '../../api/client'
import { useAuth } from '../../contexts/AuthContext'
import type { PlatformUser, PaginatedResponse } from '../../types/platform'
import { Search } from 'lucide-react'

export default function PlatformUsersPage() {
  const { user } = useAuth()
  const [users, setUsers] = useState<PlatformUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [count, setCount] = useState(0)

  const isPlatformAdmin = user?.is_platform_admin ?? false

  const fetchUsers = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const url = `/api/v1/platform/users/?search=${encodeURIComponent(search)}`
      const data = await api.get<PaginatedResponse<PlatformUser>>(url)
      setUsers(data.results)
      setCount(data.count ?? 0)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'تعذر جلب قائمة المستخدمين')
      setUsers([])
    } finally {
      setLoading(false)
    }
  }, [search])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value)
  }

  return (
    <div>
      <div style={S.header}>
        <div>
          <h1 style={S.title}>إدارة المستخدمين</h1>
          <p style={S.sub}>جميع الحسابات المسجلة في منصة GeoCabinet-DZ</p>
        </div>
      </div>

      {!isPlatformAdmin && (
        <div style={S.warningBanner}>
          ⚠️ هذه الصفحة مخصصة لمسيري المنصة فقط.
        </div>
      )}

      {error && <div style={S.err}>{error}</div>}

      <div style={S.searchBar}>
        <Search size={16} style={{ color: '#64748b' }} />
        <input
          type="text"
          placeholder="ابحث باسم أو بريد إلكتروني…"
          value={search}
          onChange={handleSearch}
          style={S.searchInput}
        />
        <span style={S.countBadge}>{count} مستخدم</span>
      </div>

      {loading && <div style={S.state}>جاري تحميل المستخدمين…</div>}

      {!loading && !error && (
        <div style={S.card}>
          <div style={S.thead}>
            <span>المستخدم</span><span>البريد الإلكتروني</span>
            <span>النوع</span><span>الحالة</span><span>العضويات</span>
          </div>
          {users.length === 0 && (
            <div style={S.empty}>لا توجد نتائج.</div>
          )}
          {users.map(u => (
            <div key={u.id} style={S.row}>
              <div style={S.userCell}>
                <div style={S.avatar}>{u.full_name.charAt(0).toUpperCase() ?? '?'}</div>
                <div style={S.userInfo}>
                  <span style={S.userName}>{u.full_name}</span>
                  <span style={S.userEmail}>{u.email}</span>
                </div>
              </div>
              <span style={S.roleLabel}>
                {u.is_platform_admin ? 'مسير المنصة' : 'مستخدم'}
              </span>
              <span style={{ ...S.roleChip, background: u.is_platform_admin ? '#e8f5e9' : '#f1f5f9', color: u.is_platform_admin ? '#2e7d32' : '#64748b' }}>
                {u.is_platform_admin ? 'مسير المنصة' : 'مستخدم'}
              </span>
              <span style={{ ...S.statusChip, background: u.is_active ? '#e8f5e9' : '#fef2f2', color: u.is_active ? '#2e7d32' : '#dc2626' }}>
                {u.is_active ? 'Actif' : 'Inactif'}
              </span>
              <span style={S.memberCount}>{u.membership_count}</span>
            </div>
          ))}
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
  searchBar: {
    display: 'flex', alignItems: 'center', gap: 12,
    background: '#fff', border: '1px solid #e2e8f0', borderRadius: 8,
    padding: '10px 16px', marginBottom: 20, width: 'fit-content',
  },
  searchInput: {
    border: 'none', outline: 'none', fontSize: 13, color: '#374151',
    width: '100%', flex: 1,
  },
  countBadge: {
    fontSize: 12, color: '#64748b', fontWeight: 500, marginLeft: 'auto',
  },
  state: { color: '#64748b', fontSize: 14, padding: 20 },
  card: { background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', overflow: 'hidden' },
  thead: {
    display: 'grid',
    gridTemplateColumns: '1fr 200px 140px 100px 100px',
    padding: '10px 20px',
    background: '#f8fafc',
    fontSize: 11, fontWeight: 600, color: '#94a3b8',
    textTransform: 'uppercase', letterSpacing: '0.05em',
  },
  row: {
    display: 'grid',
    gridTemplateColumns: '1fr 200px 140px 100px 100px',
    padding: '12px 20px',
    borderTop: '1px solid #f1f5f9',
    alignItems: 'center',
    cursor: 'pointer',
    transition: 'background 0.15s',
  },
  userCell: { display: 'flex', alignItems: 'center', gap: 10 },
  avatar: {
    width: 32, height: 32, borderRadius: '50%', background: '#e8f0fb',
    color: '#1e3a5f', display: 'flex', alignItems: 'center',
    justifyContent: 'center', fontSize: 13, fontWeight: 700, flexShrink: 0,
  },
  userInfo: { display: 'flex', flexDirection: 'column', gap: 2 },
  userName: { fontSize: 13, fontWeight: 600, color: '#1a202c' },
  userEmail: { fontSize: 12, color: '#64748b' },
  roleLabel: { fontSize: 13, color: '#64748b' },
  roleChip: {
    fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20,
    width: 'fit-content',
  },
  statusChip: {
    fontSize: 11, fontWeight: 600, padding: '3px 10px', borderRadius: 20,
    width: 'fit-content',
  },
  memberCount: { fontSize: 13, color: '#374151' },
  empty: { padding: '32px 20px', color: '#94a3b8', fontSize: 14, textAlign: 'center' },
}