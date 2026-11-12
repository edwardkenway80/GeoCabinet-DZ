-- GeoCabinet DZ — PostgreSQL 15+ / PostGIS — reviewed baseline v2
-- Initial logical/physical schema baseline. Review and run through migrations in a
-- disposable database before production deployment.
-- Tenant isolation: transaction-local app.tenant_id + RLS + tenant-scoped FKs.
-- Geometry policy: operational geometries are normalized to EPSG:4326; source_geom
-- preserves original coordinates/SRID. area_m2 is a sourced/calculated value with provenance.

BEGIN;

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS gc;
SET search_path = gc, public;

-- ---------------------------------------------------------------------------
-- 1. Platform identity and tenants
-- ---------------------------------------------------------------------------

CREATE TABLE tenants (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            varchar(180) NOT NULL,
    slug            varchar(80) NOT NULL UNIQUE,
    status          varchar(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('trial','active','suspended','closed')),
    default_locale  varchar(5) NOT NULL DEFAULT 'fr'
                    CHECK (default_locale IN ('fr','ar')),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email           varchar(254) NOT NULL,
    password_hash   text NOT NULL,
    full_name       varchar(180) NOT NULL,
    is_platform_admin boolean NOT NULL DEFAULT false,
    is_active       boolean NOT NULL DEFAULT true,
    preferred_locale varchar(5) NOT NULL DEFAULT 'fr'
                    CHECK (preferred_locale IN ('fr','ar')),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX uq_users_email_lower ON users (lower(email));

CREATE TABLE tenant_memberships (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    role_code       varchar(40) NOT NULL
                    CHECK (role_code IN ('owner','expert_director','project_manager',
                      'surveyor','cad_gis_technician','secretary','accountant','viewer')),
    is_active       boolean NOT NULL DEFAULT true,
    joined_at       timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, user_id),
    UNIQUE (tenant_id, id)
);
CREATE INDEX ix_memberships_user ON tenant_memberships(user_id, is_active);

-- Professional identity is tenant-scoped: one person may hold different roles
-- or professional credentials in different offices.
CREATE TABLE professional_profiles (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    membership_id   uuid NOT NULL,
    professional_type varchar(30) NOT NULL
                    CHECK (professional_type IN ('gef','bet_topographie','other')),
    registration_number varchar(100),
    authorization_reference varchar(150),
    authorization_valid_until date,
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------------
-- 2. Tenant-scoped reference data, parties and clients
-- ---------------------------------------------------------------------------

CREATE TABLE service_types (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    code            varchar(60) NOT NULL,
    module_code     varchar(30) NOT NULL
                    CHECK (module_code IN ('gef','topography','common')),
    name_fr         varchar(180) NOT NULL,
    name_ar         varchar(180) NOT NULL,
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, code)
);

CREATE TABLE parties (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    party_kind      varchar(20) NOT NULL CHECK (party_kind IN ('person','organization')),
    display_name    varchar(220) NOT NULL,
    first_name      varchar(100),
    last_name       varchar(100),
    organization_name varchar(220),
    national_identifier varchar(80),
    phone           varchar(40),
    email           varchar(254),
    address_text    text,
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id)
);
CREATE INDEX ix_parties_name ON parties(tenant_id, display_name);

CREATE TABLE clients (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    party_id        uuid NOT NULL,
    client_number   varchar(60) NOT NULL,
    client_status   varchar(20) NOT NULL DEFAULT 'active'
                    CHECK (client_status IN ('active','inactive','blocked')),
    tax_identifier  varchar(80),
    billing_address text,
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, client_number),
    UNIQUE (tenant_id, party_id),
    FOREIGN KEY (tenant_id, party_id)
      REFERENCES parties(tenant_id, id) ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------------
-- 3. Property and parcel registry (independent from missions)
-- ---------------------------------------------------------------------------

CREATE TABLE properties (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    property_number varchar(80) NOT NULL,
    property_kind   varchar(30) NOT NULL DEFAULT 'land'
                    CHECK (property_kind IN ('land','building','mixed','other')),
    wilaya_code     varchar(10),
    wilaya_name_fr  varchar(100),
    wilaya_name_ar  varchar(100),
    commune_code    varchar(20),
    commune_name_fr varchar(120),
    commune_name_ar varchar(120),
    locality        varchar(180),
    address_text    text,
    cadastral_reference varchar(120),
    registry_reference  varchar(120),
    geom            geometry(Geometry, 4326),
    source_geom     geometry(Geometry),
    area_m2         numeric(18,3) CHECK (area_m2 IS NULL OR area_m2 >= 0),
    area_method     varchar(40),
    area_crs        varchar(40),
    area_calculated_at timestamptz,
    source_crs      varchar(40),
    source_scale    varchar(40),
    positional_accuracy_m numeric(12,3),
    data_source     varchar(180),
    surveyed_at     date,
    registry_status varchar(30) NOT NULL DEFAULT 'unverified'
                    CHECK (registry_status IN ('unverified','working_record','reviewed','archived')),
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, property_number)
);
CREATE INDEX ix_properties_geom ON properties USING gist(geom);
CREATE INDEX ix_properties_commune ON properties(tenant_id, commune_code);

CREATE TABLE parcels (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    property_id     uuid NOT NULL,
    parcel_number   varchar(100) NOT NULL,
    cadastral_section varchar(80),
    cadastral_number  varchar(100),
    area_m2         numeric(18,3) CHECK (area_m2 IS NULL OR area_m2 >= 0),
    geom            geometry(MultiPolygon, 4326),
    source_geom     geometry(Geometry),
    area_method     varchar(40),
    area_crs        varchar(40),
    area_calculated_at timestamptz,
    source_crs      varchar(40),
    positional_accuracy_m numeric(12,3),
    valid_from      date,
    valid_to        date,
    record_status   varchar(25) NOT NULL DEFAULT 'active'
                    CHECK (record_status IN ('active','superseded','disputed','archived')),
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, property_id, parcel_number),
    FOREIGN KEY (tenant_id, property_id)
      REFERENCES properties(tenant_id, id) ON DELETE RESTRICT,
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
);
CREATE INDEX ix_parcels_geom ON parcels USING gist(geom);
CREATE INDEX ix_parcels_property ON parcels(tenant_id, property_id);

CREATE TABLE property_parties (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    property_id     uuid NOT NULL,
    party_id        uuid NOT NULL,
    relation_type   varchar(30) NOT NULL
                    CHECK (relation_type IN ('owner','co_owner','applicant','tenant',
                      'beneficiary','representative','other')),
    share_numerator bigint,
    share_denominator bigint,
    valid_from      date,
    valid_to        date,
    evidence_document_id uuid,
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, property_id)
      REFERENCES properties(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, party_id)
      REFERENCES parties(tenant_id, id) ON DELETE RESTRICT,
    CHECK ((share_numerator IS NULL AND share_denominator IS NULL) OR
           (share_numerator >= 0 AND share_denominator > 0)),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
);
CREATE INDEX ix_property_parties_property ON property_parties(tenant_id, property_id);

CREATE TABLE parcel_parties (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    parcel_id       uuid NOT NULL,
    party_id        uuid NOT NULL,
    relation_type   varchar(30) NOT NULL
                    CHECK (relation_type IN ('owner','co_owner','applicant','tenant',
                      'beneficiary','representative','other')),
    share_numerator bigint,
    share_denominator bigint,
    valid_from      date,
    valid_to        date,
    notes           text,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, parcel_id)
      REFERENCES parcels(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, party_id)
      REFERENCES parties(tenant_id, id) ON DELETE RESTRICT,
    CHECK ((share_numerator IS NULL AND share_denominator IS NULL) OR
           (share_numerator >= 0 AND share_denominator > 0)),
    CHECK (valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from)
);

-- Explicit lineage for subdivision, merger, correction and other parcel changes.
CREATE TABLE parcel_relations (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    source_parcel_id uuid NOT NULL,
    target_parcel_id uuid NOT NULL,
    relation_type   varchar(25) NOT NULL
                    CHECK (relation_type IN ('subdivided_into','merged_into','renumbered_as',
                      'corrected_to','related_to')),
    effective_date  date,
    reference_note  text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, source_parcel_id)
      REFERENCES parcels(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, target_parcel_id)
      REFERENCES parcels(tenant_id, id) ON DELETE RESTRICT,
    CHECK (source_parcel_id <> target_parcel_id)
);
CREATE INDEX ix_parcel_relations_source ON parcel_relations(tenant_id, source_parcel_id);
CREATE INDEX ix_parcel_relations_target ON parcel_relations(tenant_id, target_parcel_id);

-- ---------------------------------------------------------------------------
-- 4. Missions, workflow and assignments
-- ---------------------------------------------------------------------------

CREATE TABLE missions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_number  varchar(80) NOT NULL,
    client_id       uuid NOT NULL,
    service_type_id uuid NOT NULL,
    title           varchar(220) NOT NULL,
    description     text,
    status          varchar(25) NOT NULL DEFAULT 'lead'
                    CHECK (status IN ('lead','quoted','open','in_progress','on_hold',
                      'review','delivered','closed','cancelled')),
    priority        varchar(15) NOT NULL DEFAULT 'normal'
                    CHECK (priority IN ('low','normal','high','urgent')),
    opened_at       date,
    planned_start  date,
    due_date        date,
    closed_at       date,
    estimated_amount numeric(18,2) CHECK (estimated_amount IS NULL OR estimated_amount >= 0),
    currency_code   char(3) NOT NULL DEFAULT 'DZD',
    workflow_template_id uuid,
    created_by_membership_id uuid,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, id, workflow_template_id),
    UNIQUE (tenant_id, mission_number),
    FOREIGN KEY (tenant_id, client_id)
      REFERENCES clients(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, service_type_id)
      REFERENCES service_types(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, created_by_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    CHECK (due_date IS NULL OR planned_start IS NULL OR due_date >= planned_start)
);
CREATE INDEX ix_missions_status ON missions(tenant_id, status);
CREATE INDEX ix_missions_client ON missions(tenant_id, client_id);
CREATE INDEX ix_missions_due_date ON missions(tenant_id, due_date);

CREATE TABLE mission_properties (
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    property_id     uuid NOT NULL,
    relation_role   varchar(25) NOT NULL DEFAULT 'subject'
                    CHECK (relation_role IN ('subject','reference','neighboring','access')),
    PRIMARY KEY (tenant_id, mission_id, property_id),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, property_id)
      REFERENCES properties(tenant_id, id) ON DELETE RESTRICT
);

CREATE TABLE mission_parcels (
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    parcel_id       uuid NOT NULL,
    relation_role   varchar(25) NOT NULL DEFAULT 'subject'
                    CHECK (relation_role IN ('subject','reference','neighboring','access')),
    PRIMARY KEY (tenant_id, mission_id, parcel_id),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, parcel_id)
      REFERENCES parcels(tenant_id, id) ON DELETE RESTRICT
);

CREATE TABLE workflow_templates (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    service_type_id uuid,
    name_fr         varchar(160) NOT NULL,
    name_ar         varchar(160) NOT NULL,
    is_default      boolean NOT NULL DEFAULT false,
    is_active       boolean NOT NULL DEFAULT true,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, service_type_id)
      REFERENCES service_types(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE missions
  ADD CONSTRAINT fk_missions_workflow_template
  FOREIGN KEY (tenant_id, workflow_template_id)
  REFERENCES workflow_templates(tenant_id, id) ON DELETE RESTRICT;

CREATE TABLE workflow_template_stages (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    template_id     uuid NOT NULL,
    stage_code      varchar(50) NOT NULL,
    name_fr         varchar(160) NOT NULL,
    name_ar         varchar(160) NOT NULL,
    sequence_no     integer NOT NULL CHECK (sequence_no > 0),
    is_terminal     boolean NOT NULL DEFAULT false,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, template_id, stage_code),
    UNIQUE (tenant_id, template_id, sequence_no),
    UNIQUE (tenant_id, template_id, id),
    FOREIGN KEY (tenant_id, template_id)
      REFERENCES workflow_templates(tenant_id, id) ON DELETE CASCADE
);

CREATE TABLE mission_stages (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    workflow_template_id uuid,
    template_stage_id uuid,
    stage_code      varchar(50) NOT NULL,
    name_fr         varchar(160) NOT NULL,
    name_ar         varchar(160) NOT NULL,
    sequence_no     integer NOT NULL CHECK (sequence_no > 0),
    status          varchar(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending','active','completed','skipped','blocked')),
    started_at      timestamptz,
    completed_at    timestamptz,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, mission_id, sequence_no),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, mission_id, workflow_template_id)
      REFERENCES missions(tenant_id, id, workflow_template_id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, workflow_template_id, template_stage_id)
      REFERENCES workflow_template_stages(tenant_id, template_id, id) ON DELETE RESTRICT,
    CHECK ((workflow_template_id IS NULL) = (template_stage_id IS NULL))
);

CREATE TABLE mission_transitions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    from_status     varchar(25),
    to_status       varchar(25) NOT NULL,
    changed_by_membership_id uuid,
    reason          text,
    changed_at      timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, changed_by_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_mission_transitions_history ON mission_transitions(tenant_id, mission_id, changed_at);

CREATE TABLE mission_assignments (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    membership_id   uuid NOT NULL,
    assignment_role varchar(40) NOT NULL,
    assigned_at     timestamptz NOT NULL DEFAULT now(),
    unassigned_at   timestamptz,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    CHECK (unassigned_at IS NULL OR unassigned_at >= assigned_at)
);
CREATE INDEX ix_mission_assignments_user ON mission_assignments(tenant_id, membership_id);

CREATE TABLE tasks (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    assigned_to_membership_id uuid,
    title           varchar(220) NOT NULL,
    description     text,
    status          varchar(20) NOT NULL DEFAULT 'todo'
                    CHECK (status IN ('todo','in_progress','blocked','done','cancelled')),
    priority        varchar(15) NOT NULL DEFAULT 'normal'
                    CHECK (priority IN ('low','normal','high','urgent')),
    due_at          timestamptz,
    completed_at    timestamptz,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, assigned_to_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_tasks_assignee_status ON tasks(tenant_id, assigned_to_membership_id, status);

-- ---------------------------------------------------------------------------
-- 5. Field work, equipment and technical data
-- ---------------------------------------------------------------------------

CREATE TABLE equipment (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    asset_code      varchar(80) NOT NULL,
    equipment_type  varchar(80) NOT NULL,
    brand_model     varchar(160),
    serial_number   varchar(120),
    status          varchar(20) NOT NULL DEFAULT 'available'
                    CHECK (status IN ('available','assigned','maintenance','retired')),
    acquired_on     date,
    notes           text,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, asset_code)
);

CREATE TABLE equipment_assignments (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    equipment_id    uuid NOT NULL,
    mission_id      uuid NOT NULL,
    assigned_to_membership_id uuid,
    assigned_at     timestamptz NOT NULL DEFAULT now(),
    returned_at     timestamptz,
    condition_note  text,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, equipment_id)
      REFERENCES equipment(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, assigned_to_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    CHECK (returned_at IS NULL OR returned_at >= assigned_at)
);

CREATE TABLE field_surveys (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    survey_code     varchar(80) NOT NULL,
    survey_method   varchar(40) NOT NULL
                    CHECK (survey_method IN ('total_station','gnss','leveling','drone',
                      'mobile_gis','mixed','other')),
    survey_date     date,
    source_crs      varchar(40),
    horizontal_accuracy_m numeric(12,4),
    vertical_accuracy_m numeric(12,4),
    operator_membership_id uuid,
    notes           text,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, mission_id, survey_code),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, operator_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT
);

CREATE TABLE survey_points (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    field_survey_id uuid NOT NULL,
    point_code      varchar(80) NOT NULL,
    geom            geometry(Point, 4326) NOT NULL,
    source_geom     geometry(Point),
    elevation_m     numeric(14,4),
    point_role      varchar(40),
    source_attributes jsonb NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, field_survey_id, point_code),
    FOREIGN KEY (tenant_id, field_survey_id)
      REFERENCES field_surveys(tenant_id, id) ON DELETE CASCADE
);
CREATE INDEX ix_survey_points_geom ON survey_points USING gist(geom);

-- ---------------------------------------------------------------------------
-- 6. Documents, technical files and immutable deliverable versions
-- ---------------------------------------------------------------------------

CREATE TABLE documents (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    document_number varchar(80),
    document_type   varchar(50) NOT NULL,
    title           varchar(220) NOT NULL,
    description     text,
    confidentiality varchar(20) NOT NULL DEFAULT 'internal'
                    CHECK (confidentiality IN ('public','internal','confidential','restricted')),
    created_by_membership_id uuid,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, created_by_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT
);

ALTER TABLE property_parties
  ADD CONSTRAINT fk_property_parties_evidence_document
  FOREIGN KEY (tenant_id, evidence_document_id)
  REFERENCES documents(tenant_id, id) ON DELETE RESTRICT;

CREATE TABLE document_versions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    document_id     uuid NOT NULL,
    version_number  integer NOT NULL CHECK (version_number > 0),
    original_filename varchar(255) NOT NULL,
    storage_key     text NOT NULL,
    mime_type       varchar(150),
    file_size_bytes bigint CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
    sha256_checksum char(64) NOT NULL,
    uploaded_by_membership_id uuid,
    uploaded_at     timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, document_id, version_number),
    FOREIGN KEY (tenant_id, document_id)
      REFERENCES documents(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, uploaded_by_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT
);

-- Polymorphic linking is deliberately represented as explicit nullable FKs.
CREATE TABLE document_links (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    document_id     uuid NOT NULL,
    mission_id      uuid,
    property_id     uuid,
    parcel_id       uuid,
    client_id       uuid,
    link_role       varchar(40) NOT NULL DEFAULT 'attachment',
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, document_id)
      REFERENCES documents(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, property_id)
      REFERENCES properties(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, parcel_id)
      REFERENCES parcels(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, client_id)
      REFERENCES clients(tenant_id, id) ON DELETE RESTRICT,
    CHECK (num_nonnulls(mission_id, property_id, parcel_id, client_id) = 1)
);

CREATE TABLE technical_files (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    document_id     uuid NOT NULL,
    file_category   varchar(40) NOT NULL
                    CHECK (file_category IN ('cad_source','gis_source','raster','survey_data',
                      'calculation','report','plan','other')),
    file_format     varchar(20) NOT NULL,
    source_crs      varchar(40),
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE,
    FOREIGN KEY (tenant_id, document_id)
      REFERENCES documents(tenant_id, id) ON DELETE RESTRICT
);

CREATE TABLE deliverables (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    deliverable_type varchar(50) NOT NULL,
    title           varchar(220) NOT NULL,
    status          varchar(20) NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','under_review','approved','rejected','superseded')),
    current_version_id uuid,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE CASCADE
);

CREATE TABLE deliverable_versions (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    deliverable_id  uuid NOT NULL,
    version_number  integer NOT NULL CHECK (version_number > 0),
    document_version_id uuid NOT NULL,
    status          varchar(20) NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','submitted','approved','rejected','superseded')),
    approved_by_membership_id uuid,
    approved_at     timestamptz,
    approval_note   text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, deliverable_id, version_number),
    UNIQUE (tenant_id, deliverable_id, id),
    FOREIGN KEY (tenant_id, deliverable_id)
      REFERENCES deliverables(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, document_version_id)
      REFERENCES document_versions(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, approved_by_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    CHECK ((status = 'approved' AND approved_at IS NOT NULL) OR status <> 'approved')
);

ALTER TABLE deliverables
  ADD CONSTRAINT fk_deliverables_current_version
  FOREIGN KEY (tenant_id, id, current_version_id)
  REFERENCES deliverable_versions(tenant_id, deliverable_id, id) ON DELETE RESTRICT;

-- ---------------------------------------------------------------------------
-- 7. Quotes, invoices, payments and expenses
-- ---------------------------------------------------------------------------

CREATE TABLE quotes (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    quote_number    varchar(80) NOT NULL,
    issue_date      date NOT NULL DEFAULT CURRENT_DATE,
    valid_until     date,
    status          varchar(20) NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','sent','accepted','rejected','expired','invoiced')),
    subtotal        numeric(18,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    tax_amount      numeric(18,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    total_amount    numeric(18,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    currency_code   char(3) NOT NULL DEFAULT 'DZD',
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, quote_number),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE RESTRICT,
    CHECK (valid_until IS NULL OR valid_until >= issue_date)
);

CREATE TABLE quote_items (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    quote_id        uuid NOT NULL,
    description     text NOT NULL,
    quantity        numeric(14,3) NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price      numeric(18,2) NOT NULL CHECK (unit_price >= 0),
    line_total      numeric(18,2) NOT NULL CHECK (line_total >= 0),
    sequence_no     integer NOT NULL DEFAULT 1,
    FOREIGN KEY (tenant_id, quote_id)
      REFERENCES quotes(tenant_id, id) ON DELETE CASCADE
);

CREATE TABLE invoices (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid NOT NULL,
    quote_id        uuid,
    invoice_number  varchar(80) NOT NULL,
    issue_date      date NOT NULL DEFAULT CURRENT_DATE,
    due_date        date,
    status          varchar(20) NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','issued','partially_paid','paid','overdue','cancelled')),
    subtotal        numeric(18,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    tax_amount      numeric(18,2) NOT NULL DEFAULT 0 CHECK (tax_amount >= 0),
    total_amount    numeric(18,2) NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    currency_code   char(3) NOT NULL DEFAULT 'DZD',
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, invoice_number),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, quote_id)
      REFERENCES quotes(tenant_id, id) ON DELETE RESTRICT,
    CHECK (due_date IS NULL OR due_date >= issue_date)
);

CREATE TABLE invoice_items (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    invoice_id      uuid NOT NULL,
    description     text NOT NULL,
    quantity        numeric(14,3) NOT NULL DEFAULT 1 CHECK (quantity > 0),
    unit_price      numeric(18,2) NOT NULL CHECK (unit_price >= 0),
    line_total      numeric(18,2) NOT NULL CHECK (line_total >= 0),
    sequence_no     integer NOT NULL DEFAULT 1,
    FOREIGN KEY (tenant_id, invoice_id)
      REFERENCES invoices(tenant_id, id) ON DELETE CASCADE
);

CREATE TABLE payments (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    invoice_id      uuid NOT NULL,
    payment_reference varchar(100),
    payment_date    date NOT NULL DEFAULT CURRENT_DATE,
    amount          numeric(18,2) NOT NULL CHECK (amount > 0),
    payment_method  varchar(25) NOT NULL
                    CHECK (payment_method IN ('cash','bank_transfer','cheque','card','other')),
    status          varchar(20) NOT NULL DEFAULT 'confirmed'
                    CHECK (status IN ('pending','confirmed','reversed')),
    notes           text,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, invoice_id)
      REFERENCES invoices(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_payments_invoice ON payments(tenant_id, invoice_id, payment_date);

CREATE TABLE expenses (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    mission_id      uuid,
    expense_date    date NOT NULL DEFAULT CURRENT_DATE,
    category_code   varchar(50) NOT NULL,
    description     text,
    amount          numeric(18,2) NOT NULL CHECK (amount >= 0),
    currency_code   char(3) NOT NULL DEFAULT 'DZD',
    receipt_document_id uuid,
    created_at      timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, receipt_document_id)
      REFERENCES documents(tenant_id, id) ON DELETE RESTRICT
);

-- ---------------------------------------------------------------------------
-- 8. Audit trail
-- ---------------------------------------------------------------------------

CREATE TABLE audit_events (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tenant_id       uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    actor_membership_id uuid,
    action          varchar(60) NOT NULL,
    entity_table    varchar(100) NOT NULL,
    entity_id       uuid,
    occurred_at     timestamptz NOT NULL DEFAULT now(),
    request_id      varchar(100),
    ip_address      inet,
    before_data     jsonb,
    after_data      jsonb,
    FOREIGN KEY (tenant_id, actor_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_audit_tenant_time ON audit_events(tenant_id, occurred_at DESC);
CREATE INDEX ix_audit_entity ON audit_events(tenant_id, entity_table, entity_id);

-- Append-only protections for audit and uploaded file-version records.
CREATE OR REPLACE FUNCTION gc.reject_immutable_row_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'Rows in %.% are immutable; create a new version/event instead', TG_TABLE_SCHEMA, TG_TABLE_NAME
    USING ERRCODE = '55000';
END;
$$;

CREATE TRIGGER trg_audit_events_immutable
BEFORE UPDATE OR DELETE ON audit_events
FOR EACH ROW EXECUTE FUNCTION gc.reject_immutable_row_mutation();

CREATE TRIGGER trg_document_versions_immutable
BEFORE UPDATE OR DELETE ON document_versions
FOR EACH ROW EXECUTE FUNCTION gc.reject_immutable_row_mutation();

CREATE TRIGGER trg_deliverable_approved_immutable
BEFORE UPDATE OR DELETE ON deliverable_versions
FOR EACH ROW WHEN (OLD.status = 'approved')
EXECUTE FUNCTION gc.reject_immutable_row_mutation();

-- ---------------------------------------------------------------------------
-- 9. Tenant RLS
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION current_tenant_id()
RETURNS uuid
LANGUAGE sql
STABLE
AS $$
  SELECT NULLIF(current_setting('app.tenant_id', true), '')::uuid
$$;

-- Set the tenant context at the beginning of every request transaction:
-- SELECT set_config('app.tenant_id', '<authenticated-tenant-uuid>', true);
-- The third argument TRUE makes the setting transaction-local.

DO $$
DECLARE
    t text;
BEGIN
    FOREACH t IN ARRAY ARRAY[
      'tenant_memberships','professional_profiles','service_types','parties','clients',
      'properties','parcels','property_parties','parcel_parties','parcel_relations',
      'missions','mission_properties','mission_parcels','workflow_templates',
      'workflow_template_stages','mission_stages','mission_transitions',
      'mission_assignments','tasks','equipment','equipment_assignments','field_surveys',
      'survey_points','documents','document_versions','document_links','technical_files',
      'deliverables','deliverable_versions','quotes','quote_items','invoices',
      'invoice_items','payments','expenses','audit_events'
    ]
    LOOP
      EXECUTE format('ALTER TABLE gc.%I ENABLE ROW LEVEL SECURITY', t);
      EXECUTE format('ALTER TABLE gc.%I FORCE ROW LEVEL SECURITY', t);
      EXECUTE format(
        'CREATE POLICY tenant_isolation ON gc.%I USING (tenant_id = gc.current_tenant_id()) WITH CHECK (tenant_id = gc.current_tenant_id())',
        t
      );
    END LOOP;
END $$;

-- Important:
-- 1) tenants and users are platform-level identity tables and are not covered by
--    tenant RLS in this baseline. Expose them only through restricted backend
--    operations/views; never grant unrestricted table access to client sessions.
-- 2) The application must authenticate the user and verify an active membership
--    before setting app.tenant_id. A custom GUC is not an independent identity
--    proof; RLS is defense-in-depth against missing tenant filters and mistakes.
-- 3) Use a non-owner application DB role without BYPASSRLS. Migrations use a
--    separate privileged role. Never connect the app as a superuser/table owner.
-- 4) Tenant context must be set with SET LOCAL / set_config(..., true) inside
--    each transaction and cleared automatically at transaction end.
-- 5) Add permission checks (role/action) in the service layer; RLS isolates
--    tenants but does not replace per-role authorization.

COMMIT;
