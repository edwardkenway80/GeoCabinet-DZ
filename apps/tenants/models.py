import uuid
from django.db import models
from django.conf import settings


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    slug = models.CharField(max_length=80, unique=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('trial', 'Trial'),
            ('active', 'Active'),
            ('suspended', 'Suspended'),
            ('closed', 'Closed'),
        ],
        default='active',
    )
    default_locale = models.CharField(
        max_length=5,
        choices=[('fr', 'Français'), ('ar', 'العربية')],
        default='fr',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = '"gc"."tenants"'

    def __str__(self):
        return self.name


class TenantMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.RESTRICT,
        db_column='tenant_id',
        related_name='memberships',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.RESTRICT,
        db_column='user_id',
        related_name='memberships',
    )
    role_code = models.CharField(
        max_length=40,
        choices=[
            ('owner', 'Owner'),
            ('expert_director', 'Expert Director'),
            ('project_manager', 'Project Manager'),
            ('surveyor', 'Surveyor'),
            ('cad_gis_technician', 'CAD/GIS Technician'),
            ('secretary', 'Secretary'),
            ('accountant', 'Accountant'),
            ('viewer', 'Viewer'),
        ],
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"gc"."tenant_memberships"'
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'user'], name='uq_tenant_user'),
        ]

    def __str__(self):
        return f"{self.user.email} @ {self.tenant.name} ({self.role_code})"


class ProfessionalProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.RESTRICT,
        db_column='tenant_id',
        related_name='professional_profiles',
    )
    membership = models.ForeignKey(
        TenantMembership,
        on_delete=models.RESTRICT,
        db_column='membership_id',
        related_name='professional_profiles',
    )
    professional_type = models.CharField(
        max_length=30,
        choices=[
            ('gef', 'GEF'),
            ('bet_topographie', 'BET Topographie'),
            ('other', 'Other'),
        ],
    )
    registration_number = models.CharField(max_length=100, null=True, blank=True)
    authorization_reference = models.CharField(max_length=150, null=True, blank=True)
    authorization_valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = '"gc"."professional_profiles"'

    def __str__(self):
        return f"{self.membership.user.email} - {self.professional_type}"
