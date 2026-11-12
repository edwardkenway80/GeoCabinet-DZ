-- GeoCabinet DZ — B2B Digital Exchange — reviewed baseline v2
-- Requires 001_initial_schema_v2.sql. PostgreSQL 15+ / PostGIS.
-- Model A: each cabinet independently registers, invites and authorizes partners.
-- No public partner directory, no anonymous intake endpoint, no cross-tenant DB access.

BEGIN;
SET search_path = gc, public;

CREATE TABLE partner_organizations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    organization_name varchar(220) NOT NULL,
    organization_type varchar(40) NOT NULL CHECK (organization_type IN
      ('company','notary_office','engineering_office','public_body','supplier','client','other')),
    registration_number varchar(100),
    tax_identifier varchar(100),
    email varchar(254),
    phone varchar(40),
    address_text text,
    status varchar(20) NOT NULL DEFAULT 'invited' CHECK (status IN ('invited','active','suspended','archived')),
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id)
);
CREATE INDEX ix_partner_orgs_name ON partner_organizations(tenant_id, organization_name);

CREATE TABLE partner_contacts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    partner_organization_id uuid NOT NULL,
    full_name varchar(180) NOT NULL,
    role_title varchar(120),
    email varchar(254),
    phone varchar(40),
    is_primary boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, partner_organization_id, id),
    FOREIGN KEY (tenant_id, partner_organization_id)
      REFERENCES partner_organizations(tenant_id, id) ON DELETE RESTRICT
);
CREATE INDEX ix_partner_contacts_org ON partner_contacts(tenant_id, partner_organization_id);

-- One-time invitation proof. Only a SHA-256 hash of a high-entropy random token is stored.
CREATE TABLE partner_invitations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    partner_organization_id uuid NOT NULL,
    partner_contact_id uuid NOT NULL,
    token_hash char(64) NOT NULL UNIQUE,
    invited_by_membership_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    accepted_at timestamptz,
    revoked_at timestamptz,
    FOREIGN KEY (tenant_id, partner_organization_id, partner_contact_id)
      REFERENCES partner_contacts(tenant_id, partner_organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, invited_by_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    CHECK (expires_at > created_at),
    CHECK (accepted_at IS NULL OR revoked_at IS NULL)
);
CREATE INDEX ix_partner_invitations_pending ON partner_invitations(tenant_id, partner_organization_id, expires_at)
  WHERE accepted_at IS NULL AND revoked_at IS NULL;

CREATE TABLE external_integrations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    partner_organization_id uuid NOT NULL,
    integration_name varchar(180) NOT NULL,
    integration_type varchar(30) NOT NULL DEFAULT 'rest_api' CHECK (integration_type IN
      ('rest_api','webhook_consumer','erp','document_system','other')),
    status varchar(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','active','suspended','revoked')),
    api_version varchar(20) NOT NULL DEFAULT 'v1',
    approved_by_membership_id uuid,
    approved_at timestamptz,
    expires_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, partner_organization_id, id),
    FOREIGN KEY (tenant_id, partner_organization_id)
      REFERENCES partner_organizations(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, approved_by_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    CHECK ((approved_by_membership_id IS NULL) = (approved_at IS NULL)),
    CHECK (status <> 'active' OR approved_at IS NOT NULL)
);

CREATE TABLE api_clients (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    integration_id uuid NOT NULL,
    client_id varchar(120) NOT NULL,
    secret_hash text NOT NULL,
    scopes text[] NOT NULL DEFAULT ARRAY[]::text[],
    status varchar(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','disabled','revoked')),
    last_used_at timestamptz,
    expires_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, client_id),
    UNIQUE (tenant_id, integration_id, id),
    FOREIGN KEY (tenant_id, integration_id)
      REFERENCES external_integrations(tenant_id, id) ON DELETE RESTRICT
);

-- Pre-mission commercial/operational intake. It is not an exchange request and grants no mission access.
CREATE TABLE partner_inquiries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    partner_organization_id uuid NOT NULL,
    integration_id uuid NOT NULL,
    api_client_id uuid NOT NULL,
    external_reference varchar(120),
    request_type varchar(50) NOT NULL,
    subject varchar(220) NOT NULL,
    description text,
    requester_name varchar(180),
    requester_email varchar(254),
    requester_phone varchar(40),
    requested_service_type_id uuid,
    mapped_client_id uuid,
    status varchar(25) NOT NULL DEFAULT 'submitted' CHECK (status IN
      ('submitted','under_review','needs_information','accepted','rejected','withdrawn')),
    review_note text,
    reviewed_by_membership_id uuid,
    reviewed_at timestamptz,
    created_mission_id uuid,
    received_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, id, integration_id),
    UNIQUE (tenant_id, created_mission_id),
    UNIQUE (tenant_id, partner_organization_id, integration_id, external_reference),
    FOREIGN KEY (tenant_id, partner_organization_id, integration_id)
      REFERENCES external_integrations(tenant_id, partner_organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, integration_id, api_client_id)
      REFERENCES api_clients(tenant_id, integration_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, requested_service_type_id)
      REFERENCES service_types(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, mapped_client_id)
      REFERENCES clients(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, reviewed_by_membership_id)
      REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, created_mission_id)
      REFERENCES missions(tenant_id, id) ON DELETE RESTRICT,
    CHECK ((reviewed_by_membership_id IS NULL) = (reviewed_at IS NULL)),
    CHECK ((status = 'accepted') = (created_mission_id IS NOT NULL)),
    CHECK (status <> 'accepted' OR mapped_client_id IS NOT NULL)
);
CREATE INDEX ix_partner_inquiries_inbox ON partner_inquiries(tenant_id, status, received_at DESC);
CREATE INDEX ix_partner_inquiries_partner ON partner_inquiries(tenant_id, partner_organization_id, received_at DESC);

CREATE TABLE partner_inquiry_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    inquiry_id uuid NOT NULL,
    integration_id uuid NOT NULL,
    event_code varchar(50) NOT NULL,
    actor_type varchar(20) NOT NULL CHECK (actor_type IN ('tenant_user','partner_api','system')),
    actor_membership_id uuid,
    actor_api_client_id uuid,
    event_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, inquiry_id, integration_id) REFERENCES partner_inquiries(tenant_id, id, integration_id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, actor_membership_id) REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, integration_id, actor_api_client_id) REFERENCES api_clients(tenant_id, integration_id, id) ON DELETE RESTRICT,
    CHECK ((actor_type = 'tenant_user' AND actor_membership_id IS NOT NULL AND actor_api_client_id IS NULL) OR
           (actor_type = 'partner_api' AND actor_api_client_id IS NOT NULL AND actor_membership_id IS NULL) OR
           (actor_type = 'system' AND actor_membership_id IS NULL AND actor_api_client_id IS NULL))
);
CREATE INDEX ix_partner_inquiry_events_timeline ON partner_inquiry_events(tenant_id, inquiry_id, occurred_at);

CREATE TABLE partner_inquiry_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    inquiry_id uuid NOT NULL,
    integration_id uuid NOT NULL,
    document_version_id uuid NOT NULL,
    uploaded_by_api_client_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, inquiry_id, integration_id) REFERENCES partner_inquiries(tenant_id, id, integration_id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, document_version_id) REFERENCES document_versions(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, integration_id, uploaded_by_api_client_id) REFERENCES api_clients(tenant_id, integration_id, id) ON DELETE RESTRICT
);

-- Mission-scoped grants are integration-specific, not merely partner-specific.
CREATE TABLE partner_access_grants (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    partner_organization_id uuid NOT NULL,
    integration_id uuid NOT NULL,
    mission_id uuid NOT NULL,
    permission_code varchar(40) NOT NULL CHECK (permission_code IN
      ('request.read','request.submit','documents.upload','documents.download','deliverables.read',
       'deliverables.acknowledge','status.read')),
    granted_by_membership_id uuid NOT NULL,
    granted_at timestamptz NOT NULL DEFAULT now(),
    valid_until timestamptz,
    revoked_at timestamptz,
    revoked_by_membership_id uuid,
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, partner_organization_id, integration_id)
      REFERENCES external_integrations(tenant_id, partner_organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, mission_id) REFERENCES missions(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, granted_by_membership_id) REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, revoked_by_membership_id) REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    CHECK (valid_until IS NULL OR valid_until > granted_at),
    CHECK ((revoked_at IS NULL) = (revoked_by_membership_id IS NULL))
);
CREATE INDEX ix_partner_grants_lookup ON partner_access_grants
  (tenant_id, integration_id, mission_id, permission_code) WHERE revoked_at IS NULL;
CREATE UNIQUE INDEX uq_partner_grant_active
  ON partner_access_grants(tenant_id, integration_id, mission_id, permission_code)
  WHERE revoked_at IS NULL;

-- Once a mission exists, exchanges are always mission-bound. Pre-mission requests live above.
CREATE TABLE exchange_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    partner_organization_id uuid NOT NULL,
    integration_id uuid NOT NULL,
    mission_id uuid NOT NULL,
    request_number varchar(80) NOT NULL,
    direction varchar(12) NOT NULL CHECK (direction IN ('inbound','outbound')),
    request_type varchar(50) NOT NULL,
    subject varchar(220) NOT NULL,
    message text,
    status varchar(25) NOT NULL DEFAULT 'submitted' CHECK (status IN
      ('submitted','received','under_review','needs_information','accepted','rejected','in_progress','completed','cancelled')),
    external_reference varchar(120),
    submitted_at timestamptz NOT NULL DEFAULT now(),
    due_at timestamptz,
    created_by_membership_id uuid,
    created_by_api_client_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    UNIQUE (tenant_id, id, integration_id),
    UNIQUE (tenant_id, request_number),
    FOREIGN KEY (tenant_id, partner_organization_id, integration_id)
      REFERENCES external_integrations(tenant_id, partner_organization_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, mission_id) REFERENCES missions(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, integration_id, created_by_api_client_id)
      REFERENCES api_clients(tenant_id, integration_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, created_by_membership_id) REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    CHECK ((direction = 'inbound' AND created_by_api_client_id IS NOT NULL AND created_by_membership_id IS NULL) OR
           (direction = 'outbound' AND created_by_membership_id IS NOT NULL AND created_by_api_client_id IS NULL))
);
CREATE INDEX ix_exchange_requests_status ON exchange_requests(tenant_id, status, created_at DESC);
CREATE INDEX ix_exchange_requests_mission ON exchange_requests(tenant_id, mission_id, created_at DESC);

CREATE TABLE exchange_request_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    exchange_request_id uuid NOT NULL,
    integration_id uuid NOT NULL,
    event_code varchar(50) NOT NULL,
    old_status varchar(25),
    new_status varchar(25),
    actor_type varchar(20) NOT NULL CHECK (actor_type IN ('tenant_user','partner_api','system')),
    actor_membership_id uuid,
    actor_api_client_id uuid,
    event_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, exchange_request_id, integration_id) REFERENCES exchange_requests(tenant_id, id, integration_id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, actor_membership_id) REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, integration_id, actor_api_client_id) REFERENCES api_clients(tenant_id, integration_id, id) ON DELETE RESTRICT,
    CHECK ((actor_type = 'tenant_user' AND actor_membership_id IS NOT NULL AND actor_api_client_id IS NULL) OR
           (actor_type = 'partner_api' AND actor_api_client_id IS NOT NULL AND actor_membership_id IS NULL) OR
           (actor_type = 'system' AND actor_membership_id IS NULL AND actor_api_client_id IS NULL))
);
CREATE INDEX ix_exchange_events_timeline ON exchange_request_events(tenant_id, exchange_request_id, occurred_at);

CREATE TABLE exchange_documents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    exchange_request_id uuid NOT NULL,
    integration_id uuid NOT NULL,
    document_version_id uuid NOT NULL,
    direction varchar(12) NOT NULL CHECK (direction IN ('inbound','outbound')),
    uploaded_by_type varchar(20) NOT NULL CHECK (uploaded_by_type IN ('tenant_user','partner_api','system')),
    uploaded_by_membership_id uuid,
    uploaded_by_api_client_id uuid,
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, exchange_request_id, integration_id) REFERENCES exchange_requests(tenant_id, id, integration_id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, document_version_id) REFERENCES document_versions(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, uploaded_by_membership_id) REFERENCES tenant_memberships(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, integration_id, uploaded_by_api_client_id) REFERENCES api_clients(tenant_id, integration_id, id) ON DELETE RESTRICT,
    CHECK ((uploaded_by_type = 'tenant_user' AND uploaded_by_membership_id IS NOT NULL AND uploaded_by_api_client_id IS NULL) OR
           (uploaded_by_type = 'partner_api' AND uploaded_by_api_client_id IS NOT NULL AND uploaded_by_membership_id IS NULL) OR
           (uploaded_by_type = 'system' AND uploaded_by_membership_id IS NULL AND uploaded_by_api_client_id IS NULL))
);

CREATE TABLE webhook_subscriptions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    integration_id uuid NOT NULL,
    callback_url text NOT NULL,
    subscribed_events text[] NOT NULL CHECK (cardinality(subscribed_events) > 0),
    signing_secret_ciphertext bytea NOT NULL,
    encryption_key_version varchar(80) NOT NULL,
    status varchar(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active','paused','revoked')),
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, id),
    FOREIGN KEY (tenant_id, integration_id) REFERENCES external_integrations(tenant_id, id) ON DELETE RESTRICT
);

CREATE TABLE webhook_deliveries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    subscription_id uuid NOT NULL,
    event_id uuid,
    event_type varchar(100) NOT NULL,
    payload jsonb NOT NULL,
    status varchar(20) NOT NULL DEFAULT 'queued' CHECK (status IN ('queued','sent','failed','abandoned')),
    attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
    next_attempt_at timestamptz,
    last_http_status integer CHECK (last_http_status IS NULL OR last_http_status BETWEEN 100 AND 599),
    last_error text,
    created_at timestamptz NOT NULL DEFAULT now(),
    delivered_at timestamptz,
    FOREIGN KEY (tenant_id, subscription_id) REFERENCES webhook_subscriptions(tenant_id, id) ON DELETE RESTRICT,
    FOREIGN KEY (tenant_id, event_id) REFERENCES exchange_request_events(tenant_id, id) ON DELETE RESTRICT,
    CHECK ((status = 'sent') = (delivered_at IS NOT NULL))
);
CREATE INDEX ix_webhook_queue ON webhook_deliveries(status, next_attempt_at) WHERE status IN ('queued','failed');

CREATE TABLE api_idempotency_keys (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    api_client_id uuid NOT NULL,
    idempotency_key varchar(160) NOT NULL,
    request_hash char(64) NOT NULL,
    response_status integer CHECK (response_status IS NULL OR response_status BETWEEN 100 AND 599),
    response_body jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    UNIQUE (tenant_id, api_client_id, idempotency_key),
    FOREIGN KEY (tenant_id, api_client_id) REFERENCES api_clients(tenant_id, id) ON DELETE RESTRICT,
    CHECK (expires_at > created_at)
);
CREATE INDEX ix_api_idempotency_expiry ON api_idempotency_keys(tenant_id, expires_at);

-- Tenant-scoped RLS for every B2B table. Runtime role grants are defined separately.
DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY[
    'partner_organizations','partner_contacts','partner_invitations','external_integrations','api_clients',
    'partner_inquiries','partner_inquiry_events','partner_inquiry_documents','partner_access_grants',
    'exchange_requests','exchange_request_events','exchange_documents','webhook_subscriptions',
    'webhook_deliveries','api_idempotency_keys'
  ] LOOP
    EXECUTE format('ALTER TABLE gc.%I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE gc.%I FORCE ROW LEVEL SECURITY', t);
    EXECUTE format('CREATE POLICY tenant_isolation ON gc.%I USING (tenant_id = gc.current_tenant_id()) WITH CHECK (tenant_id = gc.current_tenant_id())', t);
  END LOOP;
END $$;

-- NOTE: application services must enforce active integration/client state, scope,
-- invitation expiry/one-time use, and a non-revoked matching grant on every call.
-- Do not trust tenant_id or partner_organization_id from API request bodies.
-- Webhook callback validation must block loopback/private/link-local/reserved IPs,
-- re-resolve DNS at delivery time, reject unsafe redirects, and enforce TLS.
-- signing_secret_ciphertext is encrypted by the application using a KMS/secret key;
-- plaintext signing secrets must never be stored or logged.

COMMIT;
