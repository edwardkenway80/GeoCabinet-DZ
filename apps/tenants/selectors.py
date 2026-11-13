from .models import Tenant, TenantMembership, ProfessionalProfile

def get_user_tenants(user):
    """جلب جميع المكاتب التي ينتمي إليها المستخدم وتكون عضويته نشطة"""
    return Tenant.objects.filter(
        memberships__user=user, 
        memberships__is_active=True
    ).distinct()

def get_user_membership(user, tenant_id):
    """جلب عضوية المستخدم في مكتب معين (للتحقق من الصلاحيات)"""
    return TenantMembership.objects.filter(
        user=user, 
        tenant_id=tenant_id, 
        is_active=True
    ).first()

def get_tenant_members(tenant):
    """جلب جميع الأعضاء النشطين في المكتب"""
    return TenantMembership.objects.filter(tenant=tenant, is_active=True)

def get_membership_professional_profile(membership):
    """جلب الملف المهني لعضوية معينة"""
    return ProfessionalProfile.objects.filter(membership=membership).first()