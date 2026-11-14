from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Tenant, TenantMembership, ProfessionalProfile

User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'status', 'default_locale', 'created_at']
        read_only_fields = ['id', 'created_at', 'status']


class TenantCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=180)
    slug = serializers.CharField(max_length=80)
    default_locale = serializers.ChoiceField(choices=['fr', 'ar'], default='fr')


MEMBER_ROLES = [
    r for r in [
        'expert_director', 'project_manager', 'surveyor',
        'cad_gis_technician', 'secretary', 'accountant', 'viewer',
    ]
]


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source='user',
        write_only=True,
    )
    role_code = serializers.ChoiceField(choices=MEMBER_ROLES)

    class Meta:
        model = TenantMembership
        fields = ['id', 'user_email', 'user_id', 'role_code', 'is_active', 'joined_at']
        read_only_fields = ['id', 'joined_at']


class ProfessionalProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfessionalProfile
        fields = [
            'id', 'professional_type', 'registration_number',
            'authorization_reference', 'authorization_valid_until', 'notes'
        ]
        read_only_fields = ['id']