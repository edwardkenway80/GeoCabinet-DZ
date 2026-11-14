export interface User {
  id: string
  email: string
  full_name: string
  is_platform_admin: boolean
  preferred_locale: string
}

export interface Tenant {
  id: string
  name: string
  slug: string
  status: 'trial' | 'active' | 'suspended' | 'closed'
  default_locale: string
  created_at: string
}

export interface Membership {
  id: string
  user_email: string
  role_code: string
  is_active: boolean
  joined_at: string
}
