import { useState } from 'react'
import { Bell, ChevronDown, LogOut } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function Topbar({ sidebarWidth }: { sidebarWidth: number }) {
  const { user, activeTenant, logout } = useAuth()
  const [open, setOpen] = useState(false)

  return (
    <header style={{ ...S.bar, left: sidebarWidth }}>
      <div style={S.office}>
        <span style={S.officeLabel}>Bureau actif</span>
        <span style={S.officeName}>{activeTenant?.name ?? '—'}</span>
      </div>
      <div style={S.right}>
        <button style={S.iconBtn}><Bell size={17} /></button>
        <div style={{ position: 'relative' }}>
          <button style={S.userBtn} onClick={() => setOpen(o => !o)}>
            <div style={S.avatar}>{user?.full_name?.charAt(0).toUpperCase() ?? '?'}</div>
            <span style={S.userName}>{user?.full_name}</span>
            <ChevronDown size={13} />
          </button>
          {open && (
            <div style={S.drop}>
              <div style={S.dropHead}>
                <div style={S.dropName}>{user?.full_name}</div>
                <div style={S.dropEmail}>{user?.email}</div>
              </div>
              <hr style={S.hr} />
              <button style={S.dropItem} onClick={() => { setOpen(false); logout() }}>
                <LogOut size={13} /> Se déconnecter
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

const S: Record<string, React.CSSProperties> = {
  bar: { position: 'fixed', top: 0, right: 0, height: 60, background: '#fff', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', zIndex: 90, transition: 'left 0.2s ease', boxShadow: '0 1px 3px rgba(0,0,0,.06)' },
  office: { display: 'flex', flexDirection: 'column', gap: 1 },
  officeLabel: { fontSize: 11, color: '#94a3b8', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' },
  officeName: { fontSize: 14, fontWeight: 600, color: '#1e3a5f' },
  right: { display: 'flex', alignItems: 'center', gap: 8 },
  iconBtn: { width: 36, height: 36, borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', cursor: 'pointer' },
  userBtn: { display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', borderRadius: 8, border: '1px solid #e2e8f0', background: '#f8fafc', cursor: 'pointer', fontSize: 13, color: '#374151' },
  avatar: { width: 28, height: 28, borderRadius: '50%', background: '#1e3a5f', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, flexShrink: 0 },
  userName: { fontWeight: 500, maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  drop: { position: 'absolute', top: '100%', right: 0, marginTop: 6, background: '#fff', border: '1px solid #e2e8f0', borderRadius: 10, boxShadow: '0 8px 24px rgba(0,0,0,.12)', minWidth: 200, zIndex: 200 },
  dropHead: { padding: '14px 16px' },
  dropName: { fontSize: 13, fontWeight: 600, color: '#1a202c' },
  dropEmail: { fontSize: 12, color: '#64748b', marginTop: 2 },
  hr: { border: 'none', borderTop: '1px solid #e2e8f0', margin: 0 },
  dropItem: { display: 'flex', alignItems: 'center', gap: 8, width: '100%', padding: '10px 16px', background: 'none', border: 'none', fontSize: 13, color: '#dc2626', cursor: 'pointer' },
}
