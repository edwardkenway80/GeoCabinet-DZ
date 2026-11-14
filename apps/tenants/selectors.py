"""
apps/tenants/selectors.py

Read-only queries for the tenants domain.

Layering contract
-----------------
- get_user_tenants()  — platform-level: uses bootstrap function, no RLS context needed.
- get_user_membership() — platform-level: uses bootstrap function, no RLS context needed.
- get_tenant_members() — tenant-scoped: caller MUST have set atomic_tenant_context()
  before calling; RLS enforces the tenant boundary at the DB level.
- get_membership_professional_profile() — tenant-scoped: same requirement.
"""

from __future__ import annotations

import uuid
from typing import Optional

from .bootstrap import get_user_memberships, verify_user_membership, BootstrappedMembership
from .models import Tenant, TenantMembership, ProfessionalProfile


def get_user_tenants(user) -> list[Tenant]:
    """
    Return all Tenant objects for which the user has an active membership.

    Uses the bootstrap function (no RLS context required).
    Returns a queryset-compatible list ordered by name.
    """
    memberships = get_user_memberships(uuid.UUID(str(user.id)))
    if not memberships:
        return Tenant.objects.none()
    tenant_ids = [m.tenant_id for m in memberships]
    return Tenant.objects.filter(id__in=tenant_ids).order_by("name")


def get_user_membership(user, tenant_id) -> Optional[BootstrappedMembership]:
    """
    Verify and return the user's active membership in tenant_id.

    Uses the bootstrap function — safe to call before RLS context is set.
    Returns None if no active membership exists.
    """
    return verify_user_membership(
        user_id=uuid.UUID(str(user.id)),
        tenant_id=uuid.UUID(str(tenant_id)),
    )


def get_tenant_members(tenant_id) -> "QuerySet[TenantMembership]":
    """
    Return active memberships for a tenant.

    REQUIRES: atomic_tenant_context(tenant_id) must be active on the caller's
    transaction. RLS will enforce the boundary; this filter is belt-and-suspenders.
    """
    return TenantMembership.objects.filter(
        tenant_id=tenant_id,
        is_active=True,
    )


def get_membership_professional_profile(
    membership: TenantMembership,
) -> Optional[ProfessionalProfile]:
    """
    Return the professional profile for a membership.

    REQUIRES: atomic_tenant_context(membership.tenant_id) must be active.
    """
    return ProfessionalProfile.objects.filter(membership=membership).first()
