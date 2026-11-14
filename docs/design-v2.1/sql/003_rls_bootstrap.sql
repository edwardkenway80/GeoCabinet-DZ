-- =============================================================================
-- GeoCabinet DZ — RLS Bootstrap Functions
-- File: docs/design-v2.1/sql/003_rls_bootstrap.sql
-- =============================================================================
-- PURPOSE
--   Provide two narrowly-scoped SECURITY DEFINER functions that allow the
--   application role (geocabinet_user) to perform operations that require
--   bypassing tenant RLS in a controlled, auditable way:
--
--   1. gc.get_user_memberships(p_user_id uuid)
--      Reads gc.tenant_memberships for a single user without app.tenant_id.
--      Used by the Django bootstrap layer to discover memberships before
--      tenant context is established.
--
--   2. gc.provision_tenant_with_owner(p_name, p_slug, p_user_id, p_locale)
--      Inserts a new tenant and its first owner membership atomically.
--      Used by the Django service layer (create_tenant_with_owner).
--      Only callable by is_platform_admin users (enforced in Django view).
--
-- SECURITY PROPERTIES
--   - Both functions are SECURITY DEFINER, owned by the role that runs this
--     script (postgres, which owns the gc schema tables).
--   - search_path is pinned to pg_catalog, gc — prevents search_path injection.
--   - All table references are schema-qualified (gc.*).
--   - EXECUTE is revoked from PUBLIC; geocabinet_user receives EXECUTE only
--     via the separate GRANT commands listed at the end of this file.
--   - Neither function accepts tenant_id from the caller as identity proof.
--
-- EXECUTION
--   Run as postgres (the table owner) on geocabinet_db:
--     \i 'D:/GeoCabinet-DZ/docs/design-v2.1/sql/003_rls_bootstrap.sql'
--   Then apply the GRANT commands separately (see bottom of this file).
--
-- DO NOT run against a production database without review.
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. gc.get_user_memberships(p_user_id uuid)
-- ---------------------------------------------------------------------------
-- Returns (tenant_id, membership_id, role_code) for a single user's active
-- memberships. Runs as the function owner (postgres), bypassing the
-- tenant_isolation RLS policy on gc.tenant_memberships.
--
-- Security:
--   - Parameterised by user_id only — cannot enumerate another user's rows.
--   - Returns only is_active = true rows.
--   - search_path pinned to pg_catalog, gc.
--   - All table references schema-qualified.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION gc.get_user_memberships(p_user_id uuid)
RETURNS TABLE (
    tenant_id     uuid,
    membership_id uuid,
    role_code     text
)
LANGUAGE sql
SECURITY DEFINER
STABLE
SET search_path = pg_catalog, gc
AS $$
    SELECT
        tm.tenant_id,
        tm.id        AS membership_id,
        tm.role_code::text
    FROM gc.tenant_memberships AS tm
    WHERE tm.user_id   = p_user_id
      AND tm.is_active = true;
$$;

REVOKE ALL ON FUNCTION gc.get_user_memberships(uuid) FROM PUBLIC;

COMMENT ON FUNCTION gc.get_user_memberships(uuid) IS
'Bootstrap: returns active memberships for one user without app.tenant_id. '
'SECURITY DEFINER. EXECUTE granted to geocabinet_user only.';


-- ---------------------------------------------------------------------------
-- 2. gc.provision_tenant_with_owner(p_name, p_slug, p_user_id, p_locale)
-- ---------------------------------------------------------------------------
-- Atomically inserts a new tenant and its first owner membership.
-- Runs as the function owner (postgres), bypassing RLS for the INSERT
-- (no valid tenant_id exists yet for a brand-new tenant).
--
-- Security:
--   - Validates user existence and is_active before any INSERT.
--   - Validates locale against the SQL CHECK constraint values.
--   - Slug uniqueness enforced by UNIQUE constraint — raises on conflict.
--   - search_path pinned to pg_catalog, gc.
--   - All table references schema-qualified.
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION gc.provision_tenant_with_owner(
    p_name    varchar(180),
    p_slug    varchar(80),
    p_user_id uuid,
    p_locale  varchar(5) DEFAULT 'fr'
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, gc
AS $$
DECLARE
    v_tenant_id uuid;
BEGIN
    IF p_locale NOT IN ('fr', 'ar') THEN
        RAISE EXCEPTION 'Invalid locale: %. Must be fr or ar.', p_locale
            USING ERRCODE = 'check_violation';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM gc.users
        WHERE id = p_user_id
          AND is_active = true
    ) THEN
        RAISE EXCEPTION 'User % does not exist or is inactive.', p_user_id
            USING ERRCODE = 'foreign_key_violation';
    END IF;

    INSERT INTO gc.tenants (name, slug, status, default_locale)
    VALUES (p_name, p_slug, 'active', p_locale)
    RETURNING id INTO v_tenant_id;

    INSERT INTO gc.tenant_memberships (tenant_id, user_id, role_code, is_active)
    VALUES (v_tenant_id, p_user_id, 'owner', true);

    RETURN v_tenant_id;
END;
$$;

REVOKE ALL ON FUNCTION
    gc.provision_tenant_with_owner(varchar, varchar, uuid, varchar)
    FROM PUBLIC;

COMMENT ON FUNCTION gc.provision_tenant_with_owner(varchar, varchar, uuid, varchar) IS
'Provisioning: atomically creates a tenant and first owner membership. '
'SECURITY DEFINER. EXECUTE granted to geocabinet_user only.';

COMMIT;

-- =============================================================================
-- GRANTS — apply separately as postgres after verifying the functions above.
-- =============================================================================
--
-- GRANT EXECUTE ON FUNCTION gc.get_user_memberships(uuid)
--     TO geocabinet_user;
--
-- GRANT EXECUTE ON FUNCTION
--     gc.provision_tenant_with_owner(varchar, varchar, uuid, varchar)
--     TO geocabinet_user;
--
-- Verify:
--   SELECT routine_name, grantee, privilege_type
--   FROM information_schema.routine_privileges
--   WHERE routine_schema = 'gc';
-- =============================================================================
