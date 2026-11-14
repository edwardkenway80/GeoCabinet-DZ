"""
apps/platform/selectors.py

Read-only selectors for the Platform Control Center.

All queries here run at platform level (no app.tenant_id RLS context).
They read from gc.tenants and gc.users which are platform-level identity tables
NOT covered by tenant RLS (see 001_initial_schema_v2.sql comments).
"""

from __future__ import annotations

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