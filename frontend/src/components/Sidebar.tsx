import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, FolderOpen, Users, Briefcase, ClipboardList,
  UserCheck, Handshake, Map, FileText, Settings, ChevronLeft, ChevronRight,
} from 'lucide-react'

interface Props {
  collapsed: boolean
  onToggle: () => void
}

const NAV = [
  { to: '/dashboard',   icon: LayoutDashboard, label: 'Tableau de bord' },
  { to: '/dossiers',    icon: FolderOpen,       label: 'Dossiers' },
  { to: '/clients',     icon: Users,            label: 'Clients' },
  { to: '/projets',     icon: Briefcase,        label: 'Projets' },
  { to: '/missions',    icon: ClipboardList,    label: 'Missions' },
  { to: '/equipe',      icon: UserCheck,        label: 'Équipe' },
  { to: '/partenaires', icon: Handshake,        label: 'Partenaires' },
  { to: '/carte',       icon: Map,              label: 'Carte' },
  { to: '/documents',   icon: FileText,         label: 'Documents' },
  { to: '/parametres',  icon: Settings,         label: 'Paramètres' },
]

export default function Sidebar({ collapsed, onToggle }: Props) {
  const w = collapsed ? 64 : 240

  return (
    <aside style={{ ...styles.sidebar, width: w }}>
      {/* Logo */}
      <div style={styles.logoRow}>
        <svg width="32" height="32" viewBox="0 0 40 40" fill="none" style={{ flexShrink: 0 }}>
          <rect width="40" height="40" rx="10" fill="#fff" opacity="0.15"/>
          <path d="M8 28L20 10L32 28H8Z" fill="white" opacity="0.9"/>
          <circle cx="20" cy="22" r="4" fill="#2e7d32"/>
        </svg>
        {!collapsed && <span style={styles.logoText}>GeoCabinet DZ</span>}
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

      {/* Collapse toggle */}
      <button onClick={onToggle} style={styles.toggle} title={collapsed ? 'Développer' : 'Réduire'}>
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>
    </aside>
  )
}

const styles: Record<string, React.CSSProperties> = {
  sidebar: {
    height: '100vh',
    background: '#1e3a5f',
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
