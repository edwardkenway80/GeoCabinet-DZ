"""
apps/tenants/services/core.py

Domain services for the tenants module.

Transaction and RLS contract
-----------------------------
create_tenant_with_owner():
    - Platform-level operation: runs WITHOUT app.tenant_id.
    - gc.tenants and gc.users are NOT covered by tenant RLS (see SQL baseline
      comment: "tenants and users are platform-level identity tables").
    - gc.tenant_memberships IS covered by RLS, but the bootstrap SQL function
      gc.provision_tenant_with_owner() runs as SECURITY DEFINER (table owner)
      so it can insert the first membership row without a tenant GUC.
    - Caller must be is_platform_admin (enforced in the view).
    - The entire operation is atomic: if membership creation fails, the tenant
      row is rolled back.

add_tenant_member():
    - Tenant-scoped: caller must pass an active atomic_tenant_context().
    - role_code 'owner' is blocked at the serializer layer; this service
      enforces it as a second line of defence.

create_professional_profile():
    - Tenant-scoped: requires atomic_tenant_context().
"""

from __future__ import annotations

import uuid

from django.db import connection, transaction
from django.core.exceptions import ValidationError

from ..models import Tenant, TenantMembership, ProfessionalProfile

# Roles that cannot be assigned via the member-add API.
_PROTECTED_ROLES = frozenset({"owner"})

# All valid role codes (mirrors SQL CHECK constraint).
_VALID_ROLES = frozenset({
    "owner", "expert_director", "project_manager",
    "surveyor", "cad_gis_technician", "secretary", "accountant", "viewer",
})


@transaction.atomic
def create_tenant_with_owner(
    *,
    name: str,
    slug: str,
    user,
    default_locale: str = "fr",
) -> Tenant:
    """
    Provision a new tenant and its first owner membership atomically.

    Uses gc.provision_tenant_with_owner() — a SECURITY DEFINER function that
    inserts into gc.tenants and gc.tenant_memberships as the table owner,
    bypassing the tenant RLS policy that would otherwise block the insert
    (because app.tenant_id is not yet set for a brand-new tenant).

    The function returns the new tenant's UUID. Django then fetches the full
    Tenant object for the response.

    Trusted provisioning path:
        1. View verifies request.user.is_platform_admin.
        2. This service calls the DB function inside @transaction.atomic.
        3. The DB function validates slug uniqueness and inserts both rows.
        4. On any DB error the transaction rolls back atomically.

    No app.tenant_id is set here — this is a platform-level operation.
    """
    with connection.cursor() as cur:
        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, %s)",
            [name, slug, str(user.id), default_locale],
        )
        row = cur.fetchone()

    if not row or not row[0]:
        raise ValidationError("فشل إنشاء المكتب في قاعدة البيانات.")

    tenant_id = row[0]
    try:
        return Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        raise ValidationError("تعذّر جلب المكتب بعد إنشائه.")


@transaction.atomic
def add_tenant_member(
    *,
    tenant: Tenant,
    user,
    role_code: str,
) -> TenantMembership:
    """
    Add a member to a tenant.

    REQUIRES: atomic_tenant_context(tenant.id) must be active on the caller's
    transaction so that RLS allows the INSERT into gc.tenant_memberships.

    role_code 'owner' is blocked here as a second line of defence (the
    serializer already excludes it from valid choices).
    """
    if role_code in _PROTECTED_ROLES:
        raise ValidationError(
            f"لا يمكن تعيين دور '{role_code}' عبر هذه الواجهة."
        )

    if role_code not in _VALID_ROLES:
        raise ValidationError(
            f"الدور غير صالح. القيم المقبولة: {sorted(_VALID_ROLES)}"
        )

    if TenantMembership.objects.filter(tenant=tenant, user=user).exists():
        raise ValidationError("هذا المستخدم عضو في المكتب بالفعل.")

    return TenantMembership.objects.create(
        tenant=tenant,
        user=user,
        role_code=role_code,
        is_active=True,
    )


@transaction.atomic
def create_professional_profile(
    *,
    tenant: Tenant,
    membership: TenantMembership,
    professional_type: str,
    **kwargs,
) -> ProfessionalProfile:
    """
    Create a professional profile for a membership.

    REQUIRES: atomic_tenant_context(tenant.id) must be active.
    """
    if membership.tenant_id != tenant.id:
        raise ValidationError("العضوية لا تنتمي إلى المكتب المحدد.")

    return ProfessionalProfile.objects.create(
        tenant=tenant,
        membership=membership,
        professional_type=professional_type,
        **kwargs,
    )
