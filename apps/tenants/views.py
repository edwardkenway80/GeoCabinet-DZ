from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Tenant, TenantMembership
from .serializers import TenantSerializer, TenantCreateSerializer, MembershipSerializer
from .selectors import get_user_tenants, get_tenant_members
from .services.core import create_tenant_with_owner, add_tenant_member
from .permissions import IsTenantAdmin

class TenantListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # جلب مكاتب المستخدم الحالي فقط
        return get_user_tenants(self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TenantCreateSerializer
        return TenantSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            tenant = create_tenant_with_owner(
                name=serializer.validated_data['name'],
                slug=serializer.validated_data['slug'],
                user=request.user,
                default_locale=serializer.validated_data.get('default_locale', 'fr')
            )
            return Response(TenantSerializer(tenant).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TenantDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsTenantAdmin]
    serializer_class = TenantSerializer
    lookup_field = 'id'
    lookup_url_kwarg = 'tenant_id'

    def get_queryset(self):
        return Tenant.objects.filter(id=self.kwargs['tenant_id'])

class MembershipListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsTenantAdmin]
    serializer_class = MembershipSerializer
    lookup_url_kwarg = 'tenant_id'

    def get_queryset(self):
        return get_tenant_members(tenant_id=self.kwargs['tenant_id'])

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            tenant = Tenant.objects.get(id=self.kwargs['tenant_id'])
            add_tenant_member(
                tenant=tenant,
                user=serializer.validated_data['user'],
                role_code=serializer.validated_data['role_code']
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)