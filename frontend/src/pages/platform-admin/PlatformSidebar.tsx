import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Building2, Users, Shield, BarChart3,
  Bell, Settings, ChevronLeft, ChevronRight, LogOut,
} from 'lucide-react'

interface Props {
  collapsed: boolean
  onToggle: () => void
  onLogout: () => void
}

const NAV = [
  { to: '/platform-admin/overview', icon: LayoutDashboard, label: 'نظرة عامة' },
  { to: '/platform-admin/bureaux', icon: Building2, label: 'المكاتب' },
  { to: '/platform-admin/users', icon: Users, label: 'المستخدمون' },
  { to: '/platform-admin/notifications', icon: Bell, label: 'الإشعارات' },
  { to: '/platform-admin/support', icon: Shield, label: 'الدعم الفني' },
  { to: '/platform-admin/communication', icon: BarChart3, label: 'التواصل' },
  { to: '/platform-admin/activity', icon: BarChart3, label: 'النشاط العام' },
  { to: '/platform-admin/security', icon: Shield, label: 'الأمن' },
  { to: '/platform-admin/monitoring', icon: BarChart3, label: 'المراقبة' },
  { to: '/platform-admin/configuration', icon: Settings, label: 'الإعدادات' },
]

export default function PlatformSidebar({ collapsed, onToggle, onLogout }: Props) {
  const w = collapsed ? 64 : 240

  return (
    <aside style={{ ...styles.sidebar, width: w }}>
      {/* Logo */}
      <div style={styles.logoRow}>
        <svg width="32" height="32" viewBox="0 0 40 40" fill="none" style={{ flexShrink: 0 }}>
          <rect width="40" height="40" rx="10" fill="#fff" opacity="0.15" />
          <path d="M8 28L20 10L32 28H8Z" fill="white" opacity="0.9" />
          <circle cx="20" cy="22" r="4" fill="#2e7d32" />
        </svg>
        {!collapsed && <span style={styles.logoText}>GeoCabinet Platform</span>}
      </div>

      {/* Nav */}
      <nav style={styles.nav}>
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            style={({ isActive }) => ({
              ...styles.link,
              background: isActive ? 'rgba(255,255,255,0.15)' : 'transparent',
              color: isActive ? '#fff' : 'rgba(255,255,255,0.7)',
            })}
            title={collapsed ? label : undefined}
          >
            <Icon size={18} style={{ flexShrink: 0 }} />
            {!collapsed && <span style={styles.linkLabel}>{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div style={styles.logoutWrap}>
        <button onClick={onLogout} style={styles.logoutBtn} title="تسجيل الخروج">
          <LogOut size={16} style={{ flexShrink: 0 }} />
          {!collapsed && <span style={styles.logoutLabel}>تسجيل الخروج</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button onClick={onToggle} style={styles.toggle} title={collapsed ? 'تطوير' : 'تقليل'}>
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </aside>
  )
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    height: '100vh',
    background: '#0f1f33',
    display: 'flex',
    flexDirection: 'column',
    position: 'fixed',
    left: 0, top: 0,
    transition: 'width 0.2s ease',
    zIndex: 100,
    overflow: 'hidden',
  },
  logoRow: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '18px 16px',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
    minHeight: 60,
  },
  logoText: {
    color: '#fff',
    fontWeight: 700,
    fontSize: '15px',
    whiteSpace: 'nowrap',
  },
  nav: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: '2px',
    padding: '12px 8px',
    overflowY: 'auto',
  },
  link: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '9px 10px',
    borderRadius: '8px',
    fontSize: '13.5px',
    fontWeight: 500,
    transition: 'background 0.15s, color 0.15s',
    whiteSpace: 'nowrap',
  },
  linkLabel: { overflow: 'hidden', textOverflow: 'ellipsis' },
  logoutWrap: {
    padding: '12px 16px',
    borderTop: '1px solid rgba(255,255,255,0.1)',
    flexShrink: 0,
  },
  logoutBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    width: '100%',
    padding: '9px 12px',
    background: 'rgba(255,255,255,0.05)',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '8px',
    color: 'rgba(255,255,255,0.7)',
    fontSize: '13px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'background 0.15s, color 0.15s',
    textAlign: 'left',
  },
  logoutLabel: { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' },
  toggle: {
    margin: '8px',
    padding: '8px',
    background: 'rgba(255,255,255,0.1)',
    border: 'none',
    borderRadius: '8px',
    color: 'rgba(255,255,255,0.7)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
  },
}