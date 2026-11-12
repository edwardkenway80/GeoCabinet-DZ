"""GeoCabinet DZ ORM mapping baseline (v2.1).

These models map the reviewed PostgreSQL schema; they do not create or alter it.
The SQL migrations remain authoritative for composite tenant foreign keys, CHECK
constraints, RLS policies, triggers, partial indexes and PostGIS-specific rules.
Django ForeignKey fields use db_constraint=False intentionally: PostgreSQL's
composite (tenant_id, object_id) constraints must remain enforced by SQL.

Requires Django 5.2+ and GeoDjango for geometry fields. Django 5.2 composite primary keys are used for the two mission junction tables. Refine ArrayField,
choices, validators, managers, permissions and querysets in the next implementation
pass. Do not run makemigrations to recreate these managed=False tables.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.contrib.gis.db import models as gis_models

class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=180)
    slug = models.CharField(max_length=80)
    status = models.CharField(max_length=20)
    default_locale = models.CharField(max_length=5)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."tenants"'
        managed = False

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.CharField(max_length=254)
    password_hash = models.TextField()
    full_name = models.CharField(max_length=180)
    is_platform_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    preferred_locale = models.CharField(max_length=5)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."users"'
        managed = False

class TenantMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    user_id = models.UUIDField()
    role_code = models.CharField(max_length=40)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."tenant_memberships"'
        managed = False

class ProfessionalProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='membership_id', db_constraint=False, null=False, blank=False)
    professional_type = models.CharField(max_length=30)
    registration_number = models.CharField(null=True, blank=True, max_length=100)
    authorization_reference = models.CharField(null=True, blank=True, max_length=150)
    authorization_valid_until = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."professional_profiles"'
        managed = False

class ServiceType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    code = models.CharField(max_length=60)
    module_code = models.CharField(max_length=30)
    name_fr = models.CharField(max_length=180)
    name_ar = models.CharField(max_length=180)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."service_types"'
        managed = False

class Party(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    party_kind = models.CharField(max_length=20)
    display_name = models.CharField(max_length=220)
    first_name = models.CharField(null=True, blank=True, max_length=100)
    last_name = models.CharField(null=True, blank=True, max_length=100)
    organization_name = models.CharField(null=True, blank=True, max_length=220)
    national_identifier = models.CharField(null=True, blank=True, max_length=80)
    phone = models.CharField(null=True, blank=True, max_length=40)
    email = models.CharField(null=True, blank=True, max_length=254)
    address_text = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."parties"'
        managed = False

class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    party = models.ForeignKey('Party', on_delete=models.PROTECT, db_column='party_id', db_constraint=False, null=False, blank=False)
    client_number = models.CharField(max_length=60)
    client_status = models.CharField(max_length=20)
    tax_identifier = models.CharField(null=True, blank=True, max_length=80)
    billing_address = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."clients"'
        managed = False

class Property(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    property_number = models.CharField(max_length=80)
    property_kind = models.CharField(max_length=30)
    wilaya_code = models.CharField(null=True, blank=True, max_length=10)
    wilaya_name_fr = models.CharField(null=True, blank=True, max_length=100)
    wilaya_name_ar = models.CharField(null=True, blank=True, max_length=100)
    commune_code = models.CharField(null=True, blank=True, max_length=20)
    commune_name_fr = models.CharField(null=True, blank=True, max_length=120)
    commune_name_ar = models.CharField(null=True, blank=True, max_length=120)
    locality = models.CharField(null=True, blank=True, max_length=180)
    address_text = models.TextField(null=True, blank=True)
    cadastral_reference = models.CharField(null=True, blank=True, max_length=120)
    registry_reference = models.CharField(null=True, blank=True, max_length=120)
    geom = gis_models.GeometryField(null=True, blank=True)
    source_geom = gis_models.GeometryField(null=True, blank=True)
    area_m2 = models.DecimalField(null=True, blank=True, max_digits=18, decimal_places=3)
    area_method = models.CharField(null=True, blank=True, max_length=40)
    area_crs = models.CharField(null=True, blank=True, max_length=40)
    area_calculated_at = models.DateTimeField(null=True, blank=True)
    source_crs = models.CharField(null=True, blank=True, max_length=40)
    source_scale = models.CharField(null=True, blank=True, max_length=40)
    positional_accuracy_m = models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=3)
    data_source = models.CharField(null=True, blank=True, max_length=180)
    surveyed_at = models.DateField(null=True, blank=True)
    registry_status = models.CharField(max_length=30)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."properties"'
        managed = False

class Parcel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    property = models.ForeignKey('Property', on_delete=models.PROTECT, db_column='property_id', db_constraint=False, null=False, blank=False)
    parcel_number = models.CharField(max_length=100)
    cadastral_section = models.CharField(null=True, blank=True, max_length=80)
    cadastral_number = models.CharField(null=True, blank=True, max_length=100)
    area_m2 = models.DecimalField(null=True, blank=True, max_digits=18, decimal_places=3)
    geom = gis_models.GeometryField(null=True, blank=True)
    source_geom = gis_models.GeometryField(null=True, blank=True)
    area_method = models.CharField(null=True, blank=True, max_length=40)
    area_crs = models.CharField(null=True, blank=True, max_length=40)
    area_calculated_at = models.DateTimeField(null=True, blank=True)
    source_crs = models.CharField(null=True, blank=True, max_length=40)
    positional_accuracy_m = models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=3)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    record_status = models.CharField(max_length=25)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."parcels"'
        managed = False

class PropertyParty(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    property = models.ForeignKey('Property', on_delete=models.PROTECT, db_column='property_id', db_constraint=False, null=False, blank=False)
    party = models.ForeignKey('Party', on_delete=models.PROTECT, db_column='party_id', db_constraint=False, null=False, blank=False)
    relation_type = models.CharField(max_length=30)
    share_numerator = models.BigIntegerField(null=True, blank=True)
    share_denominator = models.BigIntegerField(null=True, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    evidence_document_id = models.UUIDField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."property_parties"'
        managed = False

class ParcelParty(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    parcel = models.ForeignKey('Parcel', on_delete=models.PROTECT, db_column='parcel_id', db_constraint=False, null=False, blank=False)
    party = models.ForeignKey('Party', on_delete=models.PROTECT, db_column='party_id', db_constraint=False, null=False, blank=False)
    relation_type = models.CharField(max_length=30)
    share_numerator = models.BigIntegerField(null=True, blank=True)
    share_denominator = models.BigIntegerField(null=True, blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = '"gc"."parcel_parties"'
        managed = False

class ParcelRelation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    source_parcel = models.ForeignKey('Parcel', on_delete=models.PROTECT, db_column='source_parcel_id', db_constraint=False, null=False, blank=False)
    target_parcel = models.ForeignKey('Parcel', on_delete=models.PROTECT, db_column='target_parcel_id', db_constraint=False, null=False, blank=False)
    relation_type = models.CharField(max_length=25)
    effective_date = models.DateField(null=True, blank=True)
    reference_note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."parcel_relations"'
        managed = False

class Mission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission_number = models.CharField(max_length=80)
    client = models.ForeignKey('Client', on_delete=models.PROTECT, db_column='client_id', db_constraint=False, null=False, blank=False)
    service_type = models.ForeignKey('ServiceType', on_delete=models.PROTECT, db_column='service_type_id', db_constraint=False, null=False, blank=False)
    title = models.CharField(max_length=220)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=25)
    priority = models.CharField(max_length=15)
    opened_at = models.DateField(null=True, blank=True)
    planned_start = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    closed_at = models.DateField(null=True, blank=True)
    estimated_amount = models.DecimalField(null=True, blank=True, max_digits=18, decimal_places=2)
    currency_code = models.CharField(max_length=3)
    workflow_template_id = models.UUIDField(null=True, blank=True)
    created_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='created_by_membership_id', db_constraint=False, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."missions"'
        managed = False

class MissionProperty(models.Model):
    tenant_id = models.UUIDField()
    mission_id = models.UUIDField()
    property_id = models.UUIDField()
    relation_role = models.CharField(max_length=25)
    pk = models.CompositePrimaryKey('tenant_id', 'mission_id', 'property_id')

    class Meta:
        db_table = '"gc"."mission_properties"'
        managed = False

class MissionParcel(models.Model):
    tenant_id = models.UUIDField()
    mission_id = models.UUIDField()
    parcel_id = models.UUIDField()
    relation_role = models.CharField(max_length=25)
    pk = models.CompositePrimaryKey('tenant_id', 'mission_id', 'parcel_id')

    class Meta:
        db_table = '"gc"."mission_parcels"'
        managed = False

class WorkflowTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    service_type = models.ForeignKey('ServiceType', on_delete=models.PROTECT, db_column='service_type_id', db_constraint=False, null=True, blank=True)
    name_fr = models.CharField(max_length=160)
    name_ar = models.CharField(max_length=160)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = '"gc"."workflow_templates"'
        managed = False

class WorkflowTemplateStage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    template = models.ForeignKey('WorkflowTemplate', on_delete=models.PROTECT, db_column='template_id', db_constraint=False, null=False, blank=False)
    stage_code = models.CharField(max_length=50)
    name_fr = models.CharField(max_length=160)
    name_ar = models.CharField(max_length=160)
    sequence_no = models.IntegerField()
    is_terminal = models.BooleanField(default=False)

    class Meta:
        db_table = '"gc"."workflow_template_stages"'
        managed = False

class MissionStage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    workflow_template_id = models.UUIDField(null=True, blank=True)
    template_stage = models.ForeignKey('WorkflowTemplateStage', on_delete=models.PROTECT, db_column='template_stage_id', db_constraint=False, null=True, blank=True)
    stage_code = models.CharField(max_length=50)
    name_fr = models.CharField(max_length=160)
    name_ar = models.CharField(max_length=160)
    sequence_no = models.IntegerField()
    status = models.CharField(max_length=20)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = '"gc"."mission_stages"'
        managed = False

class MissionTransition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    from_status = models.CharField(null=True, blank=True, max_length=25)
    to_status = models.CharField(max_length=25)
    changed_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='changed_by_membership_id', db_constraint=False, null=True, blank=True)
    reason = models.TextField(null=True, blank=True)
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."mission_transitions"'
        managed = False

class MissionAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='membership_id', db_constraint=False, null=False, blank=False)
    assignment_role = models.CharField(max_length=40)
    assigned_at = models.DateTimeField(default=timezone.now)
    unassigned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = '"gc"."mission_assignments"'
        managed = False

class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    assigned_to_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='assigned_to_membership_id', db_constraint=False, null=True, blank=True)
    title = models.CharField(max_length=220)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20)
    priority = models.CharField(max_length=15)
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."tasks"'
        managed = False

class Equipment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    asset_code = models.CharField(max_length=80)
    equipment_type = models.CharField(max_length=80)
    brand_model = models.CharField(null=True, blank=True, max_length=160)
    serial_number = models.CharField(null=True, blank=True, max_length=120)
    status = models.CharField(max_length=20)
    acquired_on = models.DateField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = '"gc"."equipment"'
        managed = False

class EquipmentAssignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    equipment = models.ForeignKey('Equipment', on_delete=models.PROTECT, db_column='equipment_id', db_constraint=False, null=False, blank=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    assigned_to_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='assigned_to_membership_id', db_constraint=False, null=True, blank=True)
    assigned_at = models.DateTimeField(default=timezone.now)
    returned_at = models.DateTimeField(null=True, blank=True)
    condition_note = models.TextField(null=True, blank=True)

    class Meta:
        db_table = '"gc"."equipment_assignments"'
        managed = False

class FieldSurvey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    survey_code = models.CharField(max_length=80)
    survey_method = models.CharField(max_length=40)
    survey_date = models.DateField(null=True, blank=True)
    source_crs = models.CharField(null=True, blank=True, max_length=40)
    horizontal_accuracy_m = models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=4)
    vertical_accuracy_m = models.DecimalField(null=True, blank=True, max_digits=12, decimal_places=4)
    operator_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='operator_membership_id', db_constraint=False, null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    class Meta:
        db_table = '"gc"."field_surveys"'
        managed = False

class SurveyPoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    field_survey = models.ForeignKey('FieldSurvey', on_delete=models.PROTECT, db_column='field_survey_id', db_constraint=False, null=False, blank=False)
    point_code = models.CharField(max_length=80)
    geom = gis_models.GeometryField()
    source_geom = gis_models.GeometryField(null=True, blank=True)
    elevation_m = models.DecimalField(null=True, blank=True, max_digits=14, decimal_places=4)
    point_role = models.CharField(null=True, blank=True, max_length=40)
    source_attributes = models.JSONField()

    class Meta:
        db_table = '"gc"."survey_points"'
        managed = False

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    document_number = models.CharField(null=True, blank=True, max_length=80)
    document_type = models.CharField(max_length=50)
    title = models.CharField(max_length=220)
    description = models.TextField(null=True, blank=True)
    confidentiality = models.CharField(max_length=20)
    created_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='created_by_membership_id', db_constraint=False, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."documents"'
        managed = False

class DocumentVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    document = models.ForeignKey('Document', on_delete=models.PROTECT, db_column='document_id', db_constraint=False, null=False, blank=False)
    version_number = models.IntegerField()
    original_filename = models.CharField(max_length=255)
    storage_key = models.TextField()
    mime_type = models.CharField(null=True, blank=True, max_length=150)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    sha256_checksum = models.CharField(max_length=64)
    uploaded_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='uploaded_by_membership_id', db_constraint=False, null=True, blank=True)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."document_versions"'
        managed = False

class DocumentLink(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    document = models.ForeignKey('Document', on_delete=models.PROTECT, db_column='document_id', db_constraint=False, null=False, blank=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=True, blank=True)
    property = models.ForeignKey('Property', on_delete=models.PROTECT, db_column='property_id', db_constraint=False, null=True, blank=True)
    parcel = models.ForeignKey('Parcel', on_delete=models.PROTECT, db_column='parcel_id', db_constraint=False, null=True, blank=True)
    client = models.ForeignKey('Client', on_delete=models.PROTECT, db_column='client_id', db_constraint=False, null=True, blank=True)
    link_role = models.CharField(max_length=40)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."document_links"'
        managed = False

class TechnicalFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    document = models.ForeignKey('Document', on_delete=models.PROTECT, db_column='document_id', db_constraint=False, null=False, blank=False)
    file_category = models.CharField(max_length=40)
    file_format = models.CharField(max_length=20)
    source_crs = models.CharField(null=True, blank=True, max_length=40)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."technical_files"'
        managed = False

class Deliverable(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    deliverable_type = models.CharField(max_length=50)
    title = models.CharField(max_length=220)
    status = models.CharField(max_length=20)
    current_version_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."deliverables"'
        managed = False

class DeliverableVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    deliverable = models.ForeignKey('Deliverable', on_delete=models.PROTECT, db_column='deliverable_id', db_constraint=False, null=False, blank=False)
    version_number = models.IntegerField()
    document_version = models.ForeignKey('DocumentVersion', on_delete=models.PROTECT, db_column='document_version_id', db_constraint=False, null=False, blank=False)
    status = models.CharField(max_length=20)
    approved_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='approved_by_membership_id', db_constraint=False, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_note = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."deliverable_versions"'
        managed = False

class Quote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    quote_number = models.CharField(max_length=80)
    issue_date = models.DateField()
    valid_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency_code = models.CharField(max_length=3)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."quotes"'
        managed = False

class QuoteItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    quote = models.ForeignKey('Quote', on_delete=models.PROTECT, db_column='quote_id', db_constraint=False, null=False, blank=False)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=14, decimal_places=3, default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    line_total = models.DecimalField(max_digits=18, decimal_places=2)
    sequence_no = models.IntegerField(default=1)

    class Meta:
        db_table = '"gc"."quote_items"'
        managed = False

class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    quote = models.ForeignKey('Quote', on_delete=models.PROTECT, db_column='quote_id', db_constraint=False, null=True, blank=True)
    invoice_number = models.CharField(max_length=80)
    issue_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20)
    subtotal = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency_code = models.CharField(max_length=3)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."invoices"'
        managed = False

class InvoiceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    invoice = models.ForeignKey('Invoice', on_delete=models.PROTECT, db_column='invoice_id', db_constraint=False, null=False, blank=False)
    description = models.TextField()
    quantity = models.DecimalField(max_digits=14, decimal_places=3, default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    line_total = models.DecimalField(max_digits=18, decimal_places=2)
    sequence_no = models.IntegerField(default=1)

    class Meta:
        db_table = '"gc"."invoice_items"'
        managed = False

class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    invoice = models.ForeignKey('Invoice', on_delete=models.PROTECT, db_column='invoice_id', db_constraint=False, null=False, blank=False)
    payment_reference = models.CharField(null=True, blank=True, max_length=100)
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    payment_method = models.CharField(max_length=25)
    status = models.CharField(max_length=20)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."payments"'
        managed = False

class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=True, blank=True)
    expense_date = models.DateField()
    category_code = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency_code = models.CharField(max_length=3)
    receipt_document = models.ForeignKey('Document', on_delete=models.PROTECT, db_column='receipt_document_id', db_constraint=False, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."expenses"'
        managed = False

class AuditEvent(models.Model):
    id = models.BigIntegerField(primary_key=True)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    actor_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='actor_membership_id', db_constraint=False, null=True, blank=True)
    action = models.CharField(max_length=60)
    entity_table = models.CharField(max_length=100)
    entity_id = models.UUIDField(null=True, blank=True)
    occurred_at = models.DateTimeField(default=timezone.now)
    request_id = models.CharField(null=True, blank=True, max_length=100)
    ip_address = models.TextField(null=True, blank=True)
    before_data = models.JSONField(null=True, blank=True)
    after_data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = '"gc"."audit_events"'
        managed = False

class PartnerOrganization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    organization_name = models.CharField(max_length=220)
    organization_type = models.CharField(max_length=40)
    registration_number = models.CharField(null=True, blank=True, max_length=100)
    tax_identifier = models.CharField(null=True, blank=True, max_length=100)
    email = models.CharField(null=True, blank=True, max_length=254)
    phone = models.CharField(null=True, blank=True, max_length=40)
    address_text = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."partner_organizations"'
        managed = False

class PartnerContact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    partner_organization = models.ForeignKey('PartnerOrganization', on_delete=models.PROTECT, db_column='partner_organization_id', db_constraint=False, null=False, blank=False)
    full_name = models.CharField(max_length=180)
    role_title = models.CharField(null=True, blank=True, max_length=120)
    email = models.CharField(null=True, blank=True, max_length=254)
    phone = models.CharField(null=True, blank=True, max_length=40)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."partner_contacts"'
        managed = False

class PartnerInvitation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    partner_organization_id = models.UUIDField()
    partner_contact = models.ForeignKey('PartnerContact', on_delete=models.PROTECT, db_column='partner_contact_id', db_constraint=False, null=False, blank=False)
    token_hash = models.CharField(max_length=64)
    invited_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='invited_by_membership_id', db_constraint=False, null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = '"gc"."partner_invitations"'
        managed = False

class ExternalIntegration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    partner_organization = models.ForeignKey('PartnerOrganization', on_delete=models.PROTECT, db_column='partner_organization_id', db_constraint=False, null=False, blank=False)
    integration_name = models.CharField(max_length=180)
    integration_type = models.CharField(max_length=30)
    status = models.CharField(max_length=20)
    api_version = models.CharField(max_length=20)
    approved_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='approved_by_membership_id', db_constraint=False, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."external_integrations"'
        managed = False

class ApiClient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    integration = models.ForeignKey('ExternalIntegration', on_delete=models.PROTECT, db_column='integration_id', db_constraint=False, null=False, blank=False)
    client_id = models.CharField(max_length=120)
    secret_hash = models.TextField()
    scopes = models.JSONField()
    status = models.CharField(max_length=20)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."api_clients"'
        managed = False

class PartnerInquiry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    partner_organization_id = models.UUIDField()
    integration = models.ForeignKey('ExternalIntegration', on_delete=models.PROTECT, db_column='integration_id', db_constraint=False, null=False, blank=False)
    api_client = models.ForeignKey('ApiClient', on_delete=models.PROTECT, db_column='api_client_id', db_constraint=False, null=False, blank=False)
    external_reference = models.CharField(null=True, blank=True, max_length=120)
    request_type = models.CharField(max_length=50)
    subject = models.CharField(max_length=220)
    description = models.TextField(null=True, blank=True)
    requester_name = models.CharField(null=True, blank=True, max_length=180)
    requester_email = models.CharField(null=True, blank=True, max_length=254)
    requester_phone = models.CharField(null=True, blank=True, max_length=40)
    requested_service_type = models.ForeignKey('ServiceType', on_delete=models.PROTECT, db_column='requested_service_type_id', db_constraint=False, null=True, blank=True)
    mapped_client = models.ForeignKey('Client', on_delete=models.PROTECT, db_column='mapped_client_id', db_constraint=False, null=True, blank=True)
    status = models.CharField(max_length=25)
    review_note = models.TextField(null=True, blank=True)
    reviewed_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='reviewed_by_membership_id', db_constraint=False, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='created_mission_id', db_constraint=False, null=True, blank=True)
    received_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."partner_inquiries"'
        managed = False

class PartnerInquiryEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    inquiry = models.ForeignKey('PartnerInquiry', on_delete=models.PROTECT, db_column='inquiry_id', db_constraint=False, null=False, blank=False)
    integration_id = models.UUIDField()
    event_code = models.CharField(max_length=50)
    actor_type = models.CharField(max_length=20)
    actor_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='actor_membership_id', db_constraint=False, null=True, blank=True)
    actor_api_client = models.ForeignKey('ApiClient', on_delete=models.PROTECT, db_column='actor_api_client_id', db_constraint=False, null=True, blank=True)
    event_payload = models.JSONField()
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."partner_inquiry_events"'
        managed = False

class PartnerInquiryDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    inquiry = models.ForeignKey('PartnerInquiry', on_delete=models.PROTECT, db_column='inquiry_id', db_constraint=False, null=False, blank=False)
    integration_id = models.UUIDField()
    document_version = models.ForeignKey('DocumentVersion', on_delete=models.PROTECT, db_column='document_version_id', db_constraint=False, null=False, blank=False)
    uploaded_by_api_client = models.ForeignKey('ApiClient', on_delete=models.PROTECT, db_column='uploaded_by_api_client_id', db_constraint=False, null=False, blank=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."partner_inquiry_documents"'
        managed = False

class PartnerAccessGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    partner_organization_id = models.UUIDField()
    integration = models.ForeignKey('ExternalIntegration', on_delete=models.PROTECT, db_column='integration_id', db_constraint=False, null=False, blank=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    permission_code = models.CharField(max_length=40)
    granted_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='granted_by_membership_id', db_constraint=False, null=False, blank=False)
    granted_at = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='revoked_by_membership_id', db_constraint=False, null=True, blank=True)

    class Meta:
        db_table = '"gc"."partner_access_grants"'
        managed = False

class ExchangeRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    partner_organization_id = models.UUIDField()
    integration = models.ForeignKey('ExternalIntegration', on_delete=models.PROTECT, db_column='integration_id', db_constraint=False, null=False, blank=False)
    mission = models.ForeignKey('Mission', on_delete=models.PROTECT, db_column='mission_id', db_constraint=False, null=False, blank=False)
    request_number = models.CharField(max_length=80)
    direction = models.CharField(max_length=12)
    request_type = models.CharField(max_length=50)
    subject = models.CharField(max_length=220)
    message = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=25)
    external_reference = models.CharField(null=True, blank=True, max_length=120)
    submitted_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(null=True, blank=True)
    created_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='created_by_membership_id', db_constraint=False, null=True, blank=True)
    created_by_api_client = models.ForeignKey('ApiClient', on_delete=models.PROTECT, db_column='created_by_api_client_id', db_constraint=False, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."exchange_requests"'
        managed = False

class ExchangeRequestEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    exchange_request = models.ForeignKey('ExchangeRequest', on_delete=models.PROTECT, db_column='exchange_request_id', db_constraint=False, null=False, blank=False)
    integration_id = models.UUIDField()
    event_code = models.CharField(max_length=50)
    old_status = models.CharField(null=True, blank=True, max_length=25)
    new_status = models.CharField(null=True, blank=True, max_length=25)
    actor_type = models.CharField(max_length=20)
    actor_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='actor_membership_id', db_constraint=False, null=True, blank=True)
    actor_api_client = models.ForeignKey('ApiClient', on_delete=models.PROTECT, db_column='actor_api_client_id', db_constraint=False, null=True, blank=True)
    event_payload = models.JSONField()
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."exchange_request_events"'
        managed = False

class ExchangeDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    exchange_request = models.ForeignKey('ExchangeRequest', on_delete=models.PROTECT, db_column='exchange_request_id', db_constraint=False, null=False, blank=False)
    integration_id = models.UUIDField()
    document_version = models.ForeignKey('DocumentVersion', on_delete=models.PROTECT, db_column='document_version_id', db_constraint=False, null=False, blank=False)
    direction = models.CharField(max_length=12)
    uploaded_by_type = models.CharField(max_length=20)
    uploaded_by_membership = models.ForeignKey('TenantMembership', on_delete=models.PROTECT, db_column='uploaded_by_membership_id', db_constraint=False, null=True, blank=True)
    uploaded_by_api_client = models.ForeignKey('ApiClient', on_delete=models.PROTECT, db_column='uploaded_by_api_client_id', db_constraint=False, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."exchange_documents"'
        managed = False

class WebhookSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    integration = models.ForeignKey('ExternalIntegration', on_delete=models.PROTECT, db_column='integration_id', db_constraint=False, null=False, blank=False)
    callback_url = models.TextField()
    subscribed_events = models.JSONField()
    signing_secret_ciphertext = models.BinaryField()
    encryption_key_version = models.CharField(max_length=80)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = '"gc"."webhook_subscriptions"'
        managed = False

class WebhookDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    subscription = models.ForeignKey('WebhookSubscription', on_delete=models.PROTECT, db_column='subscription_id', db_constraint=False, null=False, blank=False)
    event = models.ForeignKey('ExchangeRequestEvent', on_delete=models.PROTECT, db_column='event_id', db_constraint=False, null=True, blank=True)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    status = models.CharField(max_length=20)
    attempt_count = models.IntegerField(default=0)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    last_http_status = models.IntegerField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = '"gc"."webhook_deliveries"'
        managed = False

class ApiIdempotencyKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey('Tenant', on_delete=models.PROTECT, db_column='tenant_id', db_constraint=False)
    api_client = models.ForeignKey('ApiClient', on_delete=models.PROTECT, db_column='api_client_id', db_constraint=False, null=False, blank=False)
    idempotency_key = models.CharField(max_length=160)
    request_hash = models.CharField(max_length=64)
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = '"gc"."api_idempotency_keys"'
        managed = False
