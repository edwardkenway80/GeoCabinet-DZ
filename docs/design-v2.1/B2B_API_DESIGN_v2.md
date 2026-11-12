# GeoCabinet DZ — B2B API Design (Reviewed v2)

## Product boundary
GeoCabinet is a professional office-management and controlled-interoperability layer. It does not reproduce government services, replace official portals, claim access to an undocumented government API, or become an official land/property register. The office continues to use official government portals directly. GeoCabinet manages its own clients, work files, missions, documents, internal processes, and explicitly authorized exchanges.

## Model A — per-office partner relationships
Each tenant registers its own partner organizations and contacts, invites selected contacts, approves each external software integration, issues/revokes credentials, and authorizes access. There is no global partner directory, no automatic trust between tenants, and no direct database access between organizations.

## Pre-mission intake decision
A partner may submit a limited inquiry before a mission exists, but only after the office has registered the organization/contact and issued a one-time invitation. No anonymous public intake endpoint is provided. The partner accepts the invitation, registers integration metadata, and the office approves that integration before credentials are issued. The approved integration may submit `partner_inquiries` using the `inquiries.submit` scope.

An inquiry contains only the minimum information needed for triage: request type, subject, description, requester contact details, optional requested service type, and optional attachments. It grants no access to tenant clients, properties, missions, staff, finances, or documents. The office reviews the inquiry, maps/creates the client record, and accepts or rejects it. Acceptance and mission creation occur in one transaction; the inquiry is linked to the newly created mission.

`partner_inquiries` is deliberately separate from `exchange_requests`. The latter requires an existing mission and a live, mission-scoped grant for the exact integration and permission.

## Identity and authorization chain
`tenant -> partner_organization -> external_integration -> api_client`

Mission access additionally requires a grant matching the exact `tenant_id`, `partner_organization_id`, `integration_id`, `mission_id`, permission code, validity window, and non-revoked state. API request bodies never select the tenant or partner identity; those are derived from the authenticated client. Revocation is checked on every request, not only when issuing an access token.

## API resource families
- `POST /api/v1/partner-inquiries` — submit a pre-mission inquiry (`inquiries.submit`).
- `GET /api/v1/partner-inquiries/{id}` — only the submitting integration can view its own inquiry status.
- `POST /api/v1/partner-inquiries/{id}/documents` — upload an inquiry attachment.
- `GET /api/v1/partner-inquiries/{id}/events` — limited partner-visible timeline.
- `/api/v1/missions/{id}/external-grants` — office-only grant administration.
- `/api/v1/exchange-requests` and nested events/documents — mission-bound exchange only.
- `/api/v1/webhook-subscriptions` — integration-scoped subscriptions.

Exact HTTP methods, schemas, response envelopes, rate limits and OpenAPI contract are a later API contract task; this document does not claim that endpoints are already implemented.

## Security requirements
1. OAuth 2.0 Client Credentials, short-lived tokens, secret rotation, hashed client secrets, TLS.
2. Derive tenant/partner/integration from authenticated client records.
3. Enforce active integration/client, scopes, expiry and grant revocation on each request.
4. Validate every referenced object under the same tenant and exact mission scope.
5. Use idempotency keys for write operations and request-body hashes to reject key reuse with different payloads.
6. Upload controls: size limits, MIME and file-signature validation, malware scanning, SHA-256, quarantine, and short-lived authorized download URLs.
7. Webhooks: HMAC signatures; signing secret encrypted at rest with KMS/application key; never log plaintext.
8. SSRF protection: block loopback/private/link-local/reserved IPs, re-resolve DNS at delivery, reject unsafe redirects, and require TLS.
9. Append-only inquiry/exchange/audit event history; no secret or sensitive file contents in event payloads.
10. Automated tests for tenant isolation, partner/integration mismatch, mission grant scope, expired invitation, revoked integration, replay/idempotency, and revocation.

## Rollout
- B2B-0: office-side partner registry, invitations, manual integration approval, inquiry inbox, mission-scoped grants, UI exchange.
- B2B-1: API pilot for inquiry submission and mission-bound document exchange; OpenAPI and OAuth2 client credentials.
- B2B-2: webhooks, retry queue, partner sandbox, usage dashboard.

No government integration is assumed in these phases.
