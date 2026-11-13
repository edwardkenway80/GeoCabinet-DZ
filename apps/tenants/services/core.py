from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import Tenant, TenantMembership, ProfessionalProfile

@transaction.atomic
def create_tenant_with_owner(*, name: str, slug: str, user, default_locale: str = 'fr') -> Tenant:
    """إنشاء مكتب مع عضوية مالك في معاملة واحدة (Atomic)"""
    if Tenant.objects.filter(slug=slug).exists():
        raise ValidationError(f"المكتب بالرمز '{slug}' موجود بالفعل.")
    
    tenant = Tenant.objects.create(
        name=name, 
        slug=slug, 
        default_locale=default_locale
    )
    
    TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        role_code='owner',
        is_active=True
    )
    return tenant

def add_tenant_member(*, tenant: Tenant, user, role_code: str) -> TenantMembership:
    """إضافة عضو للمكتب مع منع التكرار"""
    if TenantMembership.objects.filter(tenant=tenant, user=user).exists():
        raise ValidationError("هذا المستخدم عضو في المكتب بالفعل.")
    
    valid_roles = [r[0] for r in TenantMembership._meta.get_field('role_code').choices]
    if role_code not in valid_roles:
        raise ValidationError(f"الدور غير صالح. يجب أن يكون واحداً من: {valid_roles}")
        
    return TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        role_code=role_code,
        is_active=True
    )

def create_professional_profile(*, tenant: Tenant, membership: TenantMembership, professional_type: str, **kwargs) -> ProfessionalProfile:
    """إنشاء ملف مهني مع التحقق من تطابق العضوية مع المكتب"""
    if membership.tenant_id != tenant.id:
        raise ValidationError("العضوية لا تنتمي إلى المكتب المحدد.")
        
    return ProfessionalProfile.objects.create(
        tenant=tenant,
        membership=membership,
        professional_type=professional_type,
        **kwargs
    )