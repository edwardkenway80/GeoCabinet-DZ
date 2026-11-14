import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import PlatformSidebar from './PlatformSidebar'
import PlatformTopbar from './PlatformTopbar'
import { useAuth } from '../../contexts/AuthContext'

export default function PlatformLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const sw = collapsed ? 64 : 240
  const { logout } = useAuth()

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f4f6f9' }}>
      <PlatformSidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(c => !c)}
        onLogout={logout}
      />
      <div style={{ marginLeft: sw, flex: 1, transition: 'margin-left 0.2s ease' }}>
        <PlatformTopbar sidebarWidth={sw} />
        <main style={{ marginTop: 60, padding: '28px 32px', minHeight: 'calc(100vh - 60px)' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}