"""
apps/platform/permissions.py

DRF permissions for the Platform Control Center.

All platform-level endpoints require IsPlatformAdmin.
Platform Admin does NOT need tenant membership — is_platform_admin=True is sufficient.
"""

from rest_framework import permissions


class IsPlatformAdmin(permissions.BasePermission):
    """
    Allows access only to users with is_platform_admin=True.

    This is the gate for every Platform Control Center API.
    It does NOT consult tenant membership or RLS context.
    """

    message = "هذه العملية محصورة في مسؤولي منصة GeoCabinet."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_platform_admin
        )