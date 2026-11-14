"""
apps/platform/views.py

DRF views for the Platform Control Center.

Security contract:
- Every view requires IsPlatformAdmin permission.
- No tenant context (app.tenant_id) is opened — these are platform-level
  operations on gc.tenants and gc.users which are NOT covered by tenant RLS.
- No client-supplied tenant_id is ever trusted.
"""

from rest_framework import generics
from rest_framework.response import Response

from apps.platform.permissions import IsPlatformAdmin
from apps.platform.selectors import get_all_tenants, get_platform_stats
from apps.platform.serializers import PlatformTenantSerializer, PlatformStatsSerializer


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