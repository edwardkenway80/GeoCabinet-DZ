# GeoCabinet DZ — Consolidated Review & Decisions (v2)

## Status
Reviewed against the prior `001_initial_schema.sql`, `002_b2b_digital_exchange.sql`, `ERD.mmd`, `DATABASE_DESIGN.md` and `B2B_API_DESIGN.md`. This package is a revised design baseline, not a production-ready migration. No production database was accessed. No PostgreSQL server/client was available in the work environment, so SQL execution and RLS integration tests have not been performed.

## R1 decision — pre-mission partner intake
Adopt invitation-based intake. The office first registers a partner organization and contact, sends a one-time invitation, reviews the integration metadata, and approves the integration before issuing API credentials. Only then can the partner submit a limited `partner_inquiries` record. No anonymous/public intake endpoint.

`partner_inquiries` is separate from `exchange_requests`: inquiry is pre-mission and provides no tenant-data access; exchange request is mission-bound and requires an active grant. On acceptance, the office maps the requester to a tenant client and creates the mission in the same transaction; the inquiry stores `created_mission_id`.

## Key corrections applied
1. `clients`: uniqueness on `(tenant_id, party_id)` prevents duplicate client-role rows.
2. Workflow consistency: mission pins `workflow_template_id`; mission stages use composite FKs to the same template and its stages.
3. Deliverable consistency: composite FK ensures `current_version_id` belongs to that deliverable, not merely the same tenant.
4. Geometry provenance: source geometry retained separately; area calculation method/CRS/time fields added.
5. Technical files: storage is centralized through `documents` and `document_versions`; duplicate storage key removed.
6. Audit/document version mutation guards added; approved deliverable versions protected. Runtime role still needs explicit REVOKE/GRANT hardening.
7. B2B: partner invitation, pre-mission inquiry, inquiry events/documents, and exact integration-specific grants added.
8. Exchange requests now require an existing mission and exact partner integration; event and document actors are constrained to that same integration, with tenant-scoped candidate keys for webhook references.
10. Actor checks require the actor type to match membership/API-client/system identity columns.
11. Webhook event/subscription FKs use RESTRICT rather than dangerous composite `SET NULL`/cascade behavior; signing secret is represented as encrypted ciphertext plus key version.
13. RLS target tables and policy expressions are schema-qualified.

## Items intentionally not claimed as solved
- PostgreSQL execution, FK validation and RLS tests remain pending.
- The application must verify invitation one-time use, integration/client active status, scopes, exact grants and revocation on every request. SQL constraints cannot enforce all business authorization.
- `app.tenant_id` is not an authentication token; RLS is defense-in-depth.
- Webhook SSRF controls require application/network enforcement.
- Invoice snapshots, tax/accounting rules and a complete payment reversal ledger need a separate finance design.
- `area_m2` is not auto-calculated by the schema; calculation method and CRS must be populated by a controlled GIS service.
- Government platform coverage must be checked during product discovery before every feature is accepted. No API to فضاء الجزائر is assumed.

## Required validation before any database use
1. Create a disposable PostgreSQL 15+ database with PostGIS.
2. Apply 001 v2, then 002 v2 in a transaction; capture all errors.
3. Inspect every FK/index/check/trigger and compare with ERD.
4. Create two tenants, two users, two partners, two integrations and two missions. Attempt all cross-tenant and cross-integration references; each must fail.
5. Test RLS with the actual non-owner runtime role (not superuser/table owner), including unset/invalid tenant context and transaction-pool reuse.
6. Test invitation expiry, replay, revocation, duplicate external reference, inquiry accept/reject, atomic mission creation, and inquiry isolation.
7. Test grant scope, expiry/revocation, API client mismatch, request idempotency and webhook delivery behavior.
8. Test immutable audit/document versions and approved deliverable versions.
9. Review grants, backups/restores, object storage, signed URLs, malware scanning, secrets and operational monitoring.

## Files in this package
- `001_initial_schema_v2.sql`
- `002_b2b_digital_exchange_v2.sql`
- `ERD_v2.mmd`
- `DATABASE_DESIGN_v2.md`
- `B2B_API_DESIGN_v2.md`
