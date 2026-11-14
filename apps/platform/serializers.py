from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, TenantMembership

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


class PlatformUserSerializer(serializers.ModelSerializer):
    """
    Serializer for user listing in Platform Control Center.
    Read-only. Explicitly excludes password_hash and all sensitive auth fields.
    """

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'is_platform_admin',
            'is_active', 'preferred_locale', 'created_at',
        ]
        read_only_fields = fields


class PlatformUserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for single user details in Platform Control Center.
    Read-only. Explicitly excludes password_hash and all sensitive auth fields.
    """

    membership_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'is_platform_admin',
            'is_active', 'preferred_locale', 'created_at', 'updated_at',
            'membership_count',
        ]
        read_only_fields = fields

    def get_membership_count(self, obj):
        return obj.memberships.count()


class PlatformMembershipSerializer(serializers.ModelSerializer):
    """
    Serializer for membership listing in Platform Control Center.
    Read-only. Includes tenant and user details.
    """

    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    tenant_slug = serializers.CharField(source='tenant.slug', read_only=True)
    tenant_status = serializers.CharField(source='tenant.status', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = TenantMembership
        fields = [
            'id', 'tenant_id', 'tenant_name', 'tenant_slug', 'tenant_status',
            'user_id', 'user_email', 'user_full_name',
            'role_code', 'is_active', 'joined_at',
        ]
        read_only_fields = fields


class PlatformTenantDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for single tenant details in Platform Control Center.
    Read-only.
    """

    member_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'status', 'default_locale',
            'created_at', 'updated_at', 'member_count',
        ]
        read_only_fields = fields