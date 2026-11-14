export interface PlatformStats {
  total_tenants: number
  active_tenants: number
  suspended_tenants: number
  trial_tenants: number
  closed_tenants: number
  total_users: number
  platform_admins: number
}

export interface PlatformTenant {
  id: string
  name: string
  slug: string
  status: 'trial' | 'active' | 'suspended' | 'closed'
  default_locale: string
  created_at: string
  member_count: number
}