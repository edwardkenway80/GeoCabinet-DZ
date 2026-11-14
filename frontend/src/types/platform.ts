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
  updated_at: string
  member_count: number
}

export interface PlatformUser {
  id: string
  email: string
  full_name: string
  is_platform_admin: boolean
  is_active: boolean
  preferred_locale: string
  created_at: string
  membership_count: number
}

export interface PlatformMembership {
  id: string
  tenant_id: string
  tenant_name: string
  tenant_slug: string
  tenant_status: string
  user_id: string
  user_email: string
  user_full_name: string
  role_code: string
  is_active: boolean
  joined_at: string
}

// Paginated response wrapper
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}