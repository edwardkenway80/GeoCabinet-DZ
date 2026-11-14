"""
apps/tenants/permissions.py

DRF permission classes for the tenants domain.

IsTenantMember and IsTenantAdmin use the bootstrap membership verification
(gc.get_user_memberships) which does NOT require app.tenant_id to be set.
They store the verified BootstrappedMembership on request.membership so that
views can open atomic_tenant_context() with a trusted tenant_id.

The actual RLS enforcement happens inside the service/selector layer when
atomic_tenant_context() is entered — not here. Permissions are the gate;
RLS is the enforcement.
"""

from rest_framework import permissions

from .selectors import get_user_membership


class IsPlatformAdmin(permissions.BasePermission):
    """Allows access only to users with is_platform_admin=True."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_platform_admin
        )


class IsTenantMember(permissions.BasePermission):
    """
    Allows access only to users with an active membership in the requested tenant.

    Stores the verified BootstrappedMembership on request.membership.
    Views use request.membership.tenant_id to open atomic_tenant_context().

    Does NOT set app.tenant_id — that is the view's responsibility.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant_id = view.kwargs.get("tenant_id")
        if not tenant_id:
            # No tenant scope on this endpoint — allow authenticated access.
            return True

        membership = get_user_membership(request.user, tenant_id)
        if not membership:
            return False

        request.membership = membership
        return True


class IsTenantAdmin(IsTenantMember):
    """
    Allows access only to owner or expert_director members.

    Inherits membership verification from IsTenantMember.
    Prevents privilege escalation: role_code comes from the DB bootstrap
    function, not from client input.
    """

    ADMIN_ROLES = frozenset({"owner", "expert_director"})

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        membership = getattr(request, "membership", None)
        return membership is not None and membership.role_code in self.ADMIN_ROLES
