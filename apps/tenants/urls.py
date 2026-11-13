from django.urls import path
from .views import TenantListCreateView, TenantDetailView, MembershipListCreateView

urlpatterns = [
    path('', TenantListCreateView.as_view(), name='tenant-list-create'),
    path('<uuid:tenant_id>/', TenantDetailView.as_view(), name='tenant-detail'),
    path('<uuid:tenant_id>/members/', MembershipListCreateView.as_view(), name='membership-list-create'),
]