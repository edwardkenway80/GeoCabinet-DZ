"""
apps/platform/views.py

DRF views for the Platform Control Center.

Security contract:
- Every view requires IsPlatformAdmin permission.
- No tenant context (app.tenant_id) is opened — these are platform-level
  operations on gc.tenants, gc.users, and gc.tenant_memberships which are
  NOT covered by tenant RLS.
- No client-supplied tenant_id or user_id is ever trusted.
"""

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
import uuid

from apps.platform.permissions import IsPlatformAdmin
from apps.platform.selectors import (
    get_all_tenants, get_platform_stats,
    get_all_users, get_user_by_id, get_user_memberships_platform,
    get_tenant_by_id_platform, get_tenant_members_platform,
)
from apps.platform.serializers import (
    PlatformTenantSerializer, PlatformStatsSerializer,
    PlatformUserSerializer, PlatformUserDetailSerializer,
    PlatformMembershipSerializer, PlatformTenantDetailSerializer,
)


class PlatformTenantListView(generics.ListAPIView):
    """
    GET /api/v1/platform/tenants/

    List ALL tenants in the platform (not just the caller's memberships).
    Requires IsPlatformAdmin.
    """

    permission_classes = [IsPlatformAdmin]
    serializer_class = PlatformTenantSerializer

    def get_queryset(self):
        return get_all_tenants()


class PlatformStatsView(generics.GenericAPIView):
    """
    GET /api/v1/platform/stats/

    Aggregated platform statistics.
    Requires IsPlatformAdmin.
    """

    permission_classes = [IsPlatformAdmin]
    serializer_class = PlatformStatsSerializer

    def get(self, request, *args, **kwargs):
        stats = get_platform_stats()
        serializer = self.get_serializer(data=stats)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class PlatformUserListView(generics.ListAPIView):
    """
    GET /api/v1/platform/users/

    List ALL users in the platform.
    Supports search via ?search= query parameter.
    Requires IsPlatformAdmin.
    """

    permission_classes = [IsPlatformAdmin]
    serializer_class = PlatformUserSerializer

    def get_queryset(self):
        queryset = get_all_users()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                email__icontains=search
            ) | queryset.filter(full_name__icontains=search)
        return queryset


class PlatformUserDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/platform/users/<user_id>/

    Details of a single user.
    Requires IsPlatformAdmin.
    """

    permission_classes = [IsPlatformAdmin]
    serializer_class = PlatformUserDetailSerializer
    lookup_field = "id"
    lookup_url_kwarg = "user_id"

    def get_object(self):
        try:
            user_id = uuid.UUID(self.kwargs["user_id"])
        except (ValueError, KeyError):
            raise NotFound("Utilisateur introuvable.")
        user = get_user_by_id(user_id)
        if not user:
            raise NotFound("Utilisateur introuvable.")
        return user


class PlatformUserMembershipsView(generics.ListAPIView):
    """
    GET /api/v1/platform/users/<user_id>/memberships/

    All memberships of a user across all tenants.
    Requires IsPlatformAdmin.
    """

    permission_classes = [IsPlatformAdmin]
    serializer_class = PlatformMembershipSerializer

    def get_queryset(self):
        try:
            user_id = uuid.UUID(self.kwargs["user_id"])
        except (ValueError, KeyError):
            raise NotFound("Utilisateur introuvable.")
        # Verify user exists
        if not get_user_by_id(user_id):
            raise NotFound("Utilisateur introuvable.")
        return get_user_memberships_platform(user_id)


class PlatformTenantDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/platform/tenants/<tenant_id>/

    Details of a single tenant from Platform Admin perspective.
    Requires IsPlatformAdmin.
    """

    permission_classes = [IsPlatformAdmin]
    serializer_class = PlatformTenantDetailSerializer
    lookup_field = "id"
    lookup_url_kwarg = "tenant_id"

    def get_object(self):
        try:
            tenant_id = self.kwargs["tenant_id"]
        except (ValueError, KeyError):
            raise NotFound("Bureau introuvable.")
        tenant = get_tenant_by_id_platform(tenant_id)
        if not tenant:
            raise NotFound("Bureau introuvable.")
        return tenant


class PlatformTenantMembersView(generics.ListAPIView):
    """
    GET /api/v1/platform/tenants/<tenant_id>/members/

    All members of a tenant with their roles and statuses.
    Requires IsPlatformAdmin.
    """

    permission_classes = [IsPlatformAdmin]
    serializer_class = PlatformMembershipSerializer

    def get_queryset(self):
        try:
            tenant_id = self.kwargs["tenant_id"]
        except (ValueError, KeyError):
            raise NotFound("Bureau introuvable.")
        # Verify tenant exists
        if not get_tenant_by_id_platform(tenant_id):
            raise NotFound("Bureau introuvable.")
        return get_tenant_members_platform(tenant_id)