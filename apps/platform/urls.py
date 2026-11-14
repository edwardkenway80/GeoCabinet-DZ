from django.urls import path

from .views import PlatformTenantListView, PlatformStatsView

urlpatterns = [
    path('tenants/', PlatformTenantListView.as_view(), name='platform-tenant-list'),
    path('stats/', PlatformStatsView.as_view(), name='platform-stats'),
]