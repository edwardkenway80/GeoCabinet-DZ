from django.urls import path

from .views import (
    PlatformTenantListView,
    PlatformStatsView,
    PlatformUserListView,
    PlatformUserDetailView,
    PlatformUserMembershipsView,
    PlatformTenantDetailView,
    PlatformTenantMembersView,
)

urlpatterns = [
    path('tenants/', PlatformTenantListView.as_view(), name='platform-tenant-list'),
    path('stats/', PlatformStatsView.as_view(), name='platform-stats'),
    path('users/', PlatformUserListView.as_view(), name='platform-user-list'),
    path('users/<uuid:user_id>/', PlatformUserDetailView.as_view(), name='platform-user-detail'),
    path('users/<uuid:user_id>/memberships/', PlatformUserMembershipsView.as_view(), name='platform-user-memberships'),
    path('tenants/<uuid:tenant_id>/', PlatformTenantDetailView.as_view(), name='platform-tenant-detail'),
    path('tenants/<uuid:tenant_id>/members/', PlatformTenantMembersView.as_view(), name='platform-tenant-members'),
]