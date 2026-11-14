"""
apps/tenants/views.py

DRF views for the tenants domain.

Transaction and RLS contract
-----------------------------
- TenantListCreateView (GET): uses get_user_tenants() which calls the bootstrap
  function — no RLS context needed.
- TenantListCreateView (POST): platform-level, no RLS context.
- TenantDetailView, MembershipListCreateView: tenant-scoped operations are
  wrapped in atomic_tenant_context(request.membership.tenant_id).
  request.membership is set by IsTenantAdmin/IsTenantMember before the view
  body executes.
"""

import uuid

from django.core.exceptions import ValidationError
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.rls import atomic_tenant_context

from .models import Tenant, TenantMembership
from .permissions import IsPlatformAdmin, IsTenantAdmin
from .selectors import get_user_tenants, get_tenant_members
from .serializers import (
    MembershipSerializer,
    TenantCreateSerializer,
    TenantSerializer,
)
from .services.core import add_tenant_member, create_tenant_with_owner


class TenantListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/tenants/  — list tenants the authenticated user belongs to.
    POST /api/v1/tenants/  — provision a new tenant (platform admin only).
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Platform-level: bootstrap function, no RLS context.
        return get_user_tenants(self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TenantCreateSerializer
        return TenantSerializer

    def create(self, request, *args, **kwargs):
        if not request.user.is_platform_admin:
            return Response(
                {"detail": "إنشاء المكاتب محصور في مسؤولي المنصة."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            # Platform-level atomic — no tenant context.
            tenant = create_tenant_with_owner(
                name=serializer.validated_data["name"],
                slug=serializer.validated_data["slug"],
                user=request.user,
                default_locale=serializer.validated_data.get("default_locale", "fr"),
            )
            return Response(TenantSerializer(tenant).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)


class TenantDetailView(generics.RetrieveUpdateAPIView):
    """
    GET/PATCH /api/v1/tenants/<tenant_id>/
    Requires owner or expert_director membership.
    """

    permission_classes = [IsTenantAdmin]
    serializer_class = TenantSerializer
    lookup_field = "id"
    lookup_url_kwarg = "tenant_id"

    def get_queryset(self):
        return Tenant.objects.filter(id=self.kwargs["tenant_id"])

    def retrieve(self, request, *args, **kwargs):
        tenant_id = request.membership.tenant_id
        with atomic_tenant_context(tenant_id):
            return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        tenant_id = request.membership.tenant_id
        with atomic_tenant_context(tenant_id):
            return super().update(request, *args, **kwargs)


class MembershipListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/tenants/<tenant_id>/members/  — list active members.
    POST /api/v1/tenants/<tenant_id>/members/  — add a member.
    Requires owner or expert_director membership.
    """

    permission_classes = [IsTenantAdmin]
    serializer_class = MembershipSerializer
    lookup_url_kwarg = "tenant_id"

    def get_queryset(self):
        tenant_id = self.kwargs["tenant_id"]
        # Guard: this method must only be called from within an
        # atomic_tenant_context block (list() and create() ensure this).
        # If called outside that context, RLS returns zero rows — which is
        # the safe default. No explicit check needed; RLS enforces it.
        return get_tenant_members(tenant_id=tenant_id)

    def list(self, request, *args, **kwargs):
        tenant_id = request.membership.tenant_id
        with atomic_tenant_context(tenant_id):
            return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant_id = request.membership.tenant_id
        try:
            with atomic_tenant_context(tenant_id):
                tenant = Tenant.objects.get(id=tenant_id)
                membership = add_tenant_member(
                    tenant=tenant,
                    user=serializer.validated_data["user"],
                    role_code=serializer.validated_data["role_code"],
                )
                return Response(
                    MembershipSerializer(membership).data,
                    status=status.HTTP_201_CREATED,
                )
        except ValidationError as e:
            return Response({"detail": e.message}, status=status.HTTP_400_BAD_REQUEST)
