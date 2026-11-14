# GeoCabinet-DZ — RLS Implementation

**Version:** v2.1  
**Date:** 2025  
**Status:** Implemented — pending database owner approval for SQL grants

---

## 1. Overview

GeoCabinet-DZ uses PostgreSQL Row Level Security (RLS) as the primary tenant
isolation mechanism. Every tenant-scoped table has `FORCE ROW LEVEL SECURITY`
enabled with a policy:

```sql
USING (tenant_id = gc.current_tenant_id())
```

where `gc.current_tenant_id()` reads the transaction-local GUC `app.tenant_id`.

The Django application sets this GUC via `set_config('app.tenant_id', ..., true)`
inside atomic transactions. The `true` flag makes the setting transaction-local:
PostgreSQL clears it automatically on `COMMIT` or `ROLLBACK`.

---

## 2. Bootstrap Security Model

### The Problem

`gc.tenant_memberships` is protected by `FORCE ROW LEVEL SECURITY`. Without
`app.tenant_id` set, `geocabinet_user` sees zero rows — which is correct for
tenant-scoped queries, but prevents the initial membership lookup needed to
*establish* the context in the first place.

### Solution: Narrowly-Scoped SECURITY DEFINER Functions

Two PostgreSQL functions in `docs/design-v2.1/sql/003_rls_bootstrap.sql` run
as the table owner (`gc_owner`) and bypass RLS in a controlled way:

#### `gc.get_user_memberships(p_user_id uuid)`

Returns `(tenant_id, membership_id, role_code)` for a single user's active
memberships. Used by the Django bootstrap layer before `app.tenant_id` is set.

**Security properties:**
- Parameterised by `user_id` — cannot enumerate another user's memberships.
- Returns only `is_active = true` rows.
- `geocabinet_user` has `EXECUTE` only — no direct table access.
- `SET search_path = gc, public` inside the function prevents search-path injection.
- Django additionally verifies the returned `user_id` matches `request.user.id`
  (the authenticated session user) — `app.user_id` is never used as identity proof.

#### `gc.provision_tenant_with_owner(p_name, p_slug, p_user_id, p_locale)`

Atomically inserts a new tenant and its first owner membership. Used by
`create_tenant_with_owner()` in the Django service layer.

**Security properties:**
- Validates that `p_user_id` exists and is active before inserting.
- Validates `p_locale` against the SQL `CHECK` constraint values.
- Slug uniqueness is enforced by the `UNIQUE` constraint — raises on conflict.
- Only callable by `geocabinet_user` (after the grant is applied).
- Django view enforces `is_platform_admin` before calling this service.
- The entire operation is inside `@transaction.atomic` — partial state is impossible.

### What is NOT used as identity proof

- `app.user_id` GUC — not set, not trusted.
- Client-supplied `tenant_id` in request body or URL — always verified against
  the authenticated user's memberships via `gc.get_user_memberships` before use.

---

## 3. Transaction Lifecycle

```
HTTP Request
    │
    ├─ Django authentication (session / token)
    │   └─ request.user is the trusted identity
    │
    ├─ DRF Permission check (IsTenantMember / IsTenantAdmin)
    │   └─ calls gc.get_user_memberships(request.user.id)
    │   └─ verifies tenant_id from URL matches a returned membership
    │   └─ stores BootstrappedMembership on request.membership
    │   └─ NO app.tenant_id set yet
    │
    ├─ View enters atomic_tenant_context(request.membership.tenant_id)
    │   ├─ transaction.atomic() opens savepoint / transaction
    │   └─ set_config('app.tenant_id', tenant_id, true)
    │       └─ GUC is now transaction-local
    │
    ├─ Service / Selector executes ORM queries
    │   └─ PostgreSQL RLS enforces tenant_id = gc.current_tenant_id()
    │   └─ Cross-tenant access returns zero rows (not an error)
    │
    ├─ transaction.atomic() commits / rolls back
    │   └─ app.tenant_id cleared automatically by PostgreSQL
    │
    ├─ TenantContextCleanupMiddleware._clear_guc()
    │   └─ Belt-and-suspenders: explicit clear after response
    │   └─ Guards against savepoint reuse in connection pools
    │
    └─ HTTP Response
```

### Platform-level operations (no tenant context)

`TenantListCreateView.create` (tenant provisioning) and `TenantListCreateView.list`
(user's tenant list) do NOT set `app.tenant_id`. They operate on:
- `gc.tenants` — platform-level table, no RLS policy.
- `gc.users` — platform-level table, no RLS policy.
- `gc.get_user_memberships()` — SECURITY DEFINER, bypasses RLS safely.

---

## 4. Database Role and Grants Required

The application connects as `geocabinet_user`. This role:
- Is NOT the table owner.
- Does NOT have `BYPASSRLS`.
- Does NOT have `SUPERUSER`.
- Has `SELECT`, `INSERT`, `UPDATE`, `DELETE` on tenant-scoped tables
  (granted in the existing SQL baseline — not modified here).

### New grants required (apply manually as database owner)

These grants are in `003_rls_bootstrap.sql` but commented out. A database
owner must review and apply them:

```sql
GRANT EXECUTE ON FUNCTION gc.get_user_memberships(uuid)
    TO geocabinet_user;

GRANT EXECUTE ON FUNCTION
    gc.provision_tenant_with_owner(varchar, varchar, uuid, varchar)
    TO geocabinet_user;
```

Verify after applying:
```sql
SELECT routine_name, grantee, privilege_type
FROM information_schema.routine_privileges
WHERE routine_schema = 'gc';
```

**No other grants are required or requested.**

---

## 5. Tenant Provisioning Path

```
Platform admin (is_platform_admin=True)
    │
    POST /api/v1/tenants/
    │
    ├─ View: checks request.user.is_platform_admin → 403 if false
    ├─ Serializer: validates name, slug, default_locale
    ├─ @transaction.atomic
    │   └─ SELECT gc.provision_tenant_with_owner(name, slug, user_id, locale)
    │       ├─ Validates user exists and is active
    │       ├─ INSERT INTO gc.tenants (...)
    │       ├─ INSERT INTO gc.tenant_memberships (..., role_code='owner')
    │       └─ Returns new tenant UUID
    ├─ Django fetches Tenant object by returned UUID
    └─ Returns 201 with TenantSerializer data
```

The provisioning function runs as `gc_owner` (SECURITY DEFINER) so it can
insert the first membership row without `app.tenant_id` being set — the tenant
does not exist yet, so no valid tenant context could be established.

---

## 6. New and Modified Files

### New files

| File | Purpose |
|------|---------|
| `apps/core/rls.py` | `tenant_context()`, `atomic_tenant_context()`, `get_current_tenant_id()` |
| `apps/core/middleware.py` | `TenantContextCleanupMiddleware` — clears GUC after every response |
| `apps/tenants/bootstrap.py` | `get_user_memberships()`, `verify_user_membership()`, `BootstrappedMembership` |
| `apps/tenants/tests_rls.py` | PostgreSQL/RLS integration tests (require dedicated test DB) |
| `docs/design-v2.1/sql/003_rls_bootstrap.sql` | Bootstrap SQL functions + grant instructions |
| `docs/design-v2.1/RLS_IMPLEMENTATION.md` | This document |

### Modified files

| File | Change |
|------|--------|
| `apps/tenants/selectors.py` | Uses bootstrap function; tenant-scoped selectors require active context |
| `apps/tenants/permissions.py` | Uses `BootstrappedMembership`; added `IsPlatformAdmin` |
| `apps/tenants/services/core.py` | `create_tenant_with_owner` uses DB function; `add_tenant_member` blocks `owner` role |
| `apps/tenants/views.py` | Tenant-scoped views wrapped in `atomic_tenant_context` |
| `config/settings.py` | Registered `TenantContextCleanupMiddleware` |
| `run_tests.py` | SQLite patches for bootstrap/rls no-ops; documents test suite separation |

---

## 7. Test Results and Limitations

### SQLite smoke tests (`python run_tests.py`)

Tests business logic without PostgreSQL. Bootstrap and RLS are patched to
no-ops. These tests verify:

| Test | Result |
|------|--------|
| `test_create_tenant_with_owner` | ✓ Pass |
| `test_duplicate_slug_fails` | ✓ Pass |
| `test_add_member` | ✓ Pass |
| `test_prevent_duplicate_member` | ✓ Pass |
| `test_add_member_invalid_role_fails` | ✓ Pass |
| `test_user_sees_only_own_tenants` | ✓ Pass |
| `test_user_cannot_access_other_tenant_membership` | ✓ Pass |
| `test_inactive_membership_denied` | ✓ Pass |

**8/8 passed. These are NOT proof of RLS correctness.**

### PostgreSQL / RLS integration tests (`apps/tenants/tests_rls.py`)

**Status: NOT YET RUN — blocked on database owner approval.**

These tests require:
1. A dedicated PostgreSQL 15+ test database (not the production DB).
2. `001_initial_schema_v2.sql` applied.
3. `003_rls_bootstrap.sql` applied.
4. `GRANT EXECUTE` on both bootstrap functions to `geocabinet_user`.
5. `GC_TEST_DB_NAME` and related env vars set.

Tests cover:
- No tenant context → zero rows from `gc.tenant_memberships`.
- `gc.tenants` readable without context (platform-level table).
- `gc.get_user_memberships(user_a)` does not return `user_b`'s memberships.
- Inactive membership not returned by bootstrap function.
- Tenant A context cannot read Tenant B membership rows.
- `app.tenant_id` GUC cleared after transaction end.
- Duplicate slug raises and rolls back atomically.
- `provision_tenant_with_owner` creates exactly one tenant + one owner membership.
- Viewer role does not satisfy `IsTenantAdmin` check.

---

## 8. Operations Requiring Database Owner Approval

The following must be applied by a database owner before the application
can use the bootstrap functions:

```sql
-- Apply 003_rls_bootstrap.sql first, then:
GRANT EXECUTE ON FUNCTION gc.get_user_memberships(uuid)
    TO geocabinet_user;

GRANT EXECUTE ON FUNCTION
    gc.provision_tenant_with_owner(varchar, varchar, uuid, varchar)
    TO geocabinet_user;
```

No other database changes are required. No existing grants, RLS policies,
table ownership, or schema structure is modified by this implementation.

---

## 9. Known Limitations

- `app.tenant_id` is not an authentication token. RLS is defense-in-depth
  against missing tenant filters and programming mistakes — not a substitute
  for application-layer authorization.
- Connection pool reuse: `TenantContextCleanupMiddleware` provides a safety
  net, but the primary protection is the transaction-local GUC. If a
  connection is returned to the pool mid-transaction (which Django prevents
  by default), the GUC would persist. Use `AUTOCOMMIT=False` (Django default).
- The bootstrap function `gc.get_user_memberships` bypasses RLS by design.
  Its security depends on correct ownership (`gc_owner`) and restricted
  `EXECUTE` grants. Verify with `\df+ gc.get_user_memberships` after applying.
- `create_tenant_with_owner` currently requires `is_platform_admin`. A future
  onboarding flow may need a separate provisioning endpoint with its own
  authorization model.
