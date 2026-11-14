"""
apps/platform/selectors.py

Read-only selectors for the Platform Control Center.

All queries here run at platform level (no app.tenant_id RLS context).
They read from gc.tenants and gc.users which are platform-level identity tables
NOT covered by tenant RLS (see 001_initial_schema_v2.sql comments).
"""

from __future__ import annotations

import uuid
from typing import Optional

from django.db.models import Count, Q
from django.contrib.auth import get_user_model

from apps.tenants.models import Tenant, TenantMembership

User = get_user_model()


def get_all_tenants():
    """
    Return all tenants ordered by name.
    Safe for platform admin: no RLS context required on gc.tenants.
    Each result is annotated with active member count.
    """
    return (
        Tenant.objects.all()
        .annotate(
            member_count=Count(
                'memberships',
                filter=Q(memberships__is_active=True),
            )
        )
        .order_by('name')
    )


def get_platform_stats():
    """
    Return aggregated platform statistics.
    Reads from gc.tenants and gc.users (platform-level, no RLS).
    """
    total_tenants = Tenant.objects.count()
    by_status = (
        Tenant.objects.values('status')
        .annotate(count=Count('id'))
        .order_by('status')
    )

    status_map = {row['status']: row['count'] for row in by_status}

    total_users = User.objects.count()
    platform_admins = User.objects.filter(is_platform_admin=True).count()

    return {
        'total_tenants': total_tenants,
        'active_tenants': status_map.get('active', 0),
        'suspended_tenants': status_map.get('suspended', 0),
        'trial_tenants': status_map.get('trial', 0),
        'closed_tenants': status_map.get('closed', 0),
        'total_users': total_users,
        'platform_admins': platform_admins,
    }


def get_all_users():
    """
    Return all users ordered by email.
    Safe for platform admin: gc.users is NOT covered by tenant RLS.
    Excludes password_hash automatically via serializer.
    """
    return User.objects.all().order_by('email')


def get_user_by_id(user_id: uuid.UUID) -> Optional[User]:
    """
    Return a single user by ID, or None if not found.
    Safe for platform admin: gc.users is NOT covered by tenant RLS.
    """
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None


def get_user_memberships_platform(user_id: uuid.UUID):
    """
    Return all active memberships for a user across all tenants,
    with tenant name and slug included.
    Safe for platform admin: gc.tenant_memberships read at platform level
    (no app.tenant_id context required for this selector).
    """
    return (
        TenantMembership.objects.filter(user_id=user_id, is_active=True)
        .select_related('tenant')
        .order_by('tenant__name')
    )


def get_tenant_by_id_platform(tenant_id: uuid.UUID) -> Optional[Tenant]:
    """
    Return a single tenant by ID, or None if not found.
    Safe for platform admin: gc.tenants is NOT covered by tenant RLS.
    """
    try:
        return Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return None


def get_tenant_members_platform(tenant_id: uuid.UUID):
    """
    Return all memberships for a tenant with user details.
    Safe for platform admin: reads gc.tenant_memberships and gc.users
    at platform level (no app.tenant_id context required).
    """
    return (
        TenantMembership.objects.filter(tenant_id=tenant_id)
        .select_related('user')
        .order_by('user__email')
    )