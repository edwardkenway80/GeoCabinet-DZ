from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant

User = get_user_model()


class PlatformTenantSerializer(serializers.ModelSerializer):
    """
    Serializer for tenant listing in Platform Control Center.
    Read-only fields: id, created_at, status.
    """

    member_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'status', 'default_locale',
            'created_at', 'member_count',
        ]
        read_only_fields = fields


class PlatformStatsSerializer(serializers.Serializer):
    """
    Aggregated platform statistics (read-only).
    """

    total_tenants = serializers.IntegerField()
    active_tenants = serializers.IntegerField()
    suspended_tenants = serializers.IntegerField()
    trial_tenants = serializers.IntegerField()
    closed_tenants = serializers.IntegerField()
    total_users = serializers.IntegerField()
    platform_admins = serializers.IntegerField()