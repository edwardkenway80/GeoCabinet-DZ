import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const sw = collapsed ? 64 : 240

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f4f6f9' }}>
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(c => !c)} />
      <div style={{ marginLeft: sw, flex: 1, transition: 'margin-left 0.2s ease' }}>
        <Topbar sidebarWidth={sw} />
        <main style={{ marginTop: 60, padding: '28px 32px', minHeight: 'calc(100vh - 60px)' }}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
