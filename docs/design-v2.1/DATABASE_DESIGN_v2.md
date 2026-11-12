# GeoCabinet DZ — Database Design (Reviewed v2)

## 1. Product boundary
GeoCabinet manages the internal operations of surveying, land-expertise and topographic-study offices and provides controlled interoperability with their business partners. It does not duplicate state-provided digital services, replace official portals (including فضاء الجزائر), assume undocumented government APIs, act as an official land-title/cadastre register, or replace CAD/GIS/surveying specialist applications. Government portals remain external systems used directly by the office.

Before adding a feature, apply this gate: (a) does an official Algerian platform already provide it? (b) would this feature duplicate or compete with a public service? If yes, exclude it or limit GeoCabinet to lawful internal workflow/documentation around the service; do not assume API access.

## 2. Architecture
Cloud SaaS first; Local Deployment remains a future target. PostgreSQL 15+ / PostGIS, Django + DRF modular monolith, React + TypeScript + MapLibre, OpenAPI, S3-compatible object storage adapter. Tenant is one independent office. Arabic and French from v1. UUID identifiers.

## 3. Core model corrections
- `clients` has one client-role row per party per tenant.
- `missions.workflow_template_id` pins the selected workflow template; `mission_stages` can only reference stages from that same template.
- `deliverable_versions` exposes a composite key `(tenant_id, deliverable_id, id)` so a deliverable's current version cannot belong to another deliverable.
- `technical_files` points to a logical `documents` record; actual file bytes and immutable versions live only in `document_versions`, avoiding duplicate storage keys.
- Properties/parcels/survey points preserve original geometry separately from normalized EPSG:4326 operational geometry. `area_m2` carries calculation method/CRS/time provenance and must not be computed as planar area in EPSG:4326.
- Audit events and uploaded document versions have database-level mutation guards; approved deliverable versions cannot be overwritten. Runtime grants must also deny update/delete.

## 4. B2B Model A
Each office registers its own partner organizations and contacts, sends a one-time invitation, approves external integrations, and issues credentials. No public partner directory and no cross-tenant trust.

Pre-mission requests are `partner_inquiries`, accepted only from an invited and approved integration. They have no mission and grant no access to office data. The office reviews, maps the requester to a tenant client, and atomically creates a mission when accepting. `exchange_requests` are distinct and always require an existing mission plus a live integration-specific grant.

## 5. Tenant isolation
Every tenant-owned table carries `tenant_id`. Composite foreign keys prevent cross-tenant references. RLS is enabled and forced on tenant tables; backend authentication/authorization remains mandatory. `app.tenant_id` is a transaction context value, not proof of identity. Use a non-owner runtime role without BYPASSRLS, parameterized queries, verified membership before setting transaction-local context, and automated two-tenant tests. Do not expose database credentials to clients.

`users` and `tenants` remain platform-level tables outside tenant RLS; access them through narrowly granted backend operations. Production role grants and secret management must be separately reviewed.

## 6. B2B authorization
Authorization chain: tenant -> partner organization -> integration -> API client. Mission permissions are bound to exact integration + mission + permission + validity/revocation. Never trust tenant or partner IDs from request bodies. Check integration/client state, scope and grant on every request. Invitation tokens are high-entropy, one-time and stored only as hashes. Webhook signing secrets must be encrypted at rest because delivery requires recovering the secret to sign payloads.

## 7. Known non-goals / outstanding production work
- No government API integration assumed.
- No legal validity claim for e-signatures or exchanged documents.
- No complete Algerian accounting/tax engine. Invoice snapshots, payment reversal ledger, tax treatment and regulatory review remain required.
- Runtime DB roles/grants, signed URL policy, malware scanning, webhook SSRF defenses, backup/restore, tenant export/retention and data-protection review remain go-live requirements.
- No live PostgreSQL execution was performed for this reviewed file set; execute only in a disposable test database after independent SQL review.
