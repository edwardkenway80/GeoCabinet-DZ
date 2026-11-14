import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { api, clearCsrfCache } from '../api/client'
import type { User, Tenant } from '../types'

interface AuthState {
  user: User | null
  tenants: Tenant[]
  activeTenant: Tenant | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  selectTenant: (tenant: Tenant) => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [tenants, setTenants] = useState<Tenant[]>([])
  const [activeTenant, setActiveTenant] = useState<Tenant | null>(null)
  const [loading, setLoading] = useState(true)

  // On mount: check if session already exists
  useEffect(() => {
    api.get<User>('/api/v1/auth/me/')
      .then(async (u) => {
        setUser(u)
        await loadTenants()
      })
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  async function loadTenants() {
    try {
      const list = await api.get<Tenant[]>('/api/v1/tenants/')
      setTenants(list)
      if (list.length === 1) setActiveTenant(list[0])
    } catch {
      setTenants([])
    }
  }

  async function login(email: string, password: string) {
    const u = await api.post<User>('/api/v1/auth/login/', { email, password })
    setUser(u)
    await loadTenants()
  }

  async function logout() {
    await api.post('/api/v1/auth/logout/', {})
    clearCsrfCache()
    setUser(null)
    setTenants([])
    setActiveTenant(null)
  }

  function selectTenant(tenant: Tenant) {
    // Only allow selecting a tenant the user actually belongs to
    if (tenants.find(t => t.id === tenant.id)) {
      setActiveTenant(tenant)
    }
  }

  return (
    <AuthContext.Provider value={{ user, tenants, activeTenant, loading, login, logout, selectTenant }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
