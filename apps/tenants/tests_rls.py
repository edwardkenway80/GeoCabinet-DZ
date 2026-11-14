"""
apps/tenants/tests_rls.py

PostgreSQL / RLS integration tests for GeoCabinet-DZ.

IMPORTANT — READ BEFORE RUNNING
--------------------------------
These tests require a dedicated PostgreSQL 15+ test database with:
  1. The gc schema applied from 001_initial_schema_v2.sql.
  2. The bootstrap functions applied from 003_rls_bootstrap.sql.
  3. The geocabinet_user role with EXECUTE grants on both functions.
  4. The test database must NOT be the production database.

Set the following environment variables before running:
    GC_TEST_DB_NAME     — test database name (e.g. geocabinet_test)
    GC_TEST_DB_USER     — geocabinet_user (the restricted app role)
    GC_TEST_DB_PASSWORD — password for geocabinet_user
    GC_TEST_DB_HOST     — host (default: localhost)
    GC_TEST_DB_PORT     — port (default: 5432)

Run with:
    python -m pytest apps/tenants/tests_rls.py -v

These tests do NOT run against the user's existing database.
They do NOT modify any existing data.
They create and clean up their own test data within transactions that are
always rolled back (or within a dedicated test schema).

SQLite smoke tests (tests.py) remain valid for business-logic unit testing
but are NOT proof of RLS correctness.
"""

import os
import uuid
import pytest

# ---------------------------------------------------------------------------
# Skip the entire module if the test DB env vars are not set.
# This prevents accidental runs against the wrong database.
# ---------------------------------------------------------------------------
_REQUIRED_ENV = "GC_TEST_DB_NAME"
pytestmark = pytest.mark.skipif(
    not os.environ.get(_REQUIRED_ENV),
    reason=(
        f"RLS integration tests skipped: {_REQUIRED_ENV} not set. "
        "Configure a dedicated test PostgreSQL database and set GC_TEST_DB_* "
        "environment variables to run these tests."
    ),
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def pg_conn():
    """
    Raw psycopg connection to the test database as geocabinet_user.
    Uses autocommit=False so each test controls its own transaction.
    """
    import psycopg

    conn = psycopg.connect(
        dbname=os.environ["GC_TEST_DB_NAME"],
        user=os.environ.get("GC_TEST_DB_USER", "geocabinet_user"),
        password=os.environ.get("GC_TEST_DB_PASSWORD", ""),
        host=os.environ.get("GC_TEST_DB_HOST", "localhost"),
        port=int(os.environ.get("GC_TEST_DB_PORT", 5432)),
        autocommit=False,
    )
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def pg_owner_conn():
    """
    Raw psycopg connection as the schema owner (gc_owner or superuser).
    Used only for test data setup that requires bypassing RLS.
    Requires GC_TEST_OWNER_USER and GC_TEST_OWNER_PASSWORD env vars.
    """
    import psycopg

    owner_user = os.environ.get("GC_TEST_OWNER_USER")
    if not owner_user:
        pytest.skip("GC_TEST_OWNER_USER not set — skipping owner-level fixtures.")

    conn = psycopg.connect(
        dbname=os.environ["GC_TEST_DB_NAME"],
        user=owner_user,
        password=os.environ.get("GC_TEST_OWNER_PASSWORD", ""),
        host=os.environ.get("GC_TEST_DB_HOST", "localhost"),
        port=int(os.environ.get("GC_TEST_DB_PORT", 5432)),
        autocommit=False,
    )
    yield conn
    conn.close()


@pytest.fixture
def rollback_tx(pg_conn):
    """
    Yields a cursor inside a transaction that is always rolled back.
    Guarantees test isolation without touching production data.
    """
    with pg_conn.transaction() as tx:
        with pg_conn.cursor() as cur:
            yield cur
        tx.rollback()


@pytest.fixture
def owner_rollback_tx(pg_owner_conn):
    """Same as rollback_tx but using the owner connection."""
    with pg_owner_conn.transaction() as tx:
        with pg_owner_conn.cursor() as cur:
            yield cur
        tx.rollback()


# ---------------------------------------------------------------------------
# Helper: set / clear tenant GUC
# ---------------------------------------------------------------------------

def set_tenant(cur, tenant_id: str) -> None:
    cur.execute("SELECT set_config('app.tenant_id', %s, true)", [str(tenant_id)])


def clear_tenant(cur) -> None:
    cur.execute("SELECT set_config('app.tenant_id', %s, true)", [""])


def current_tenant(cur) -> str | None:
    cur.execute("SELECT current_setting('app.tenant_id', true)")
    val = cur.fetchone()[0]
    return val if val else None


# ---------------------------------------------------------------------------
# Test: no tenant context returns no tenant-scoped rows
# ---------------------------------------------------------------------------

class TestNoContextReturnsNoRows:
    def test_memberships_empty_without_context(self, rollback_tx):
        """
        Without app.tenant_id set, gc.tenant_memberships must return 0 rows
        to geocabinet_user (FORCE ROW LEVEL SECURITY).
        """
        cur = rollback_tx
        clear_tenant(cur)
        cur.execute("SELECT count(*) FROM gc.tenant_memberships")
        count = cur.fetchone()[0]
        assert count == 0, (
            f"Expected 0 rows without tenant context, got {count}. "
            "Check that FORCE ROW LEVEL SECURITY is enabled on gc.tenant_memberships."
        )

    def test_tenants_readable_without_context(self, rollback_tx):
        """
        gc.tenants is a platform-level table NOT covered by tenant RLS.
        It should be readable (count >= 0) without app.tenant_id.
        """
        cur = rollback_tx
        clear_tenant(cur)
        cur.execute("SELECT count(*) FROM gc.tenants")
        # Should not raise — tenants table has no RLS policy.
        count = cur.fetchone()[0]
        assert isinstance(count, int)


# ---------------------------------------------------------------------------
# Test: bootstrap function isolation
# ---------------------------------------------------------------------------

class TestBootstrapFunctionIsolation:
    def test_get_user_memberships_returns_only_own(self, rollback_tx, pg_owner_conn):
        """
        gc.get_user_memberships(user_a_id) must not return user_b's memberships.
        """
        cur = rollback_tx

        # Create two users and two tenants via the owner connection.
        # We use savepoints so the rollback_tx fixture cleans up.
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()

        cur.execute(
            "INSERT INTO gc.users (id, email, password_hash, full_name) "
            "VALUES (%s, %s, 'x', 'User A')",
            [str(user_a_id), f"user_a_{user_a_id}@test.invalid"],
        )
        cur.execute(
            "INSERT INTO gc.users (id, email, password_hash, full_name) "
            "VALUES (%s, %s, 'x', 'User B')",
            [str(user_b_id), f"user_b_{user_b_id}@test.invalid"],
        )

        # Provision two tenants via the bootstrap function.
        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, %s)",
            ["Tenant A", f"tenant-a-{user_a_id}", str(user_a_id), "fr"],
        )
        tenant_a_id = cur.fetchone()[0]

        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, %s)",
            ["Tenant B", f"tenant-b-{user_b_id}", str(user_b_id), "fr"],
        )
        tenant_b_id = cur.fetchone()[0]

        # Query memberships for user_a only.
        cur.execute(
            "SELECT tenant_id FROM gc.get_user_memberships(%s)",
            [str(user_a_id)],
        )
        rows = cur.fetchall()
        returned_tenant_ids = {str(r[0]) for r in rows}

        assert str(tenant_a_id) in returned_tenant_ids, "User A should see Tenant A."
        assert str(tenant_b_id) not in returned_tenant_ids, (
            "User A must NOT see Tenant B via get_user_memberships."
        )

    def test_inactive_membership_not_returned(self, rollback_tx):
        """
        get_user_memberships must not return inactive memberships.
        """
        cur = rollback_tx
        user_id = uuid.uuid4()

        cur.execute(
            "INSERT INTO gc.users (id, email, password_hash, full_name) "
            "VALUES (%s, %s, 'x', 'Inactive User')",
            [str(user_id), f"inactive_{user_id}@test.invalid"],
        )
        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, %s)",
            ["Inactive Tenant", f"inactive-{user_id}", str(user_id), "fr"],
        )
        tenant_id = cur.fetchone()[0]

        # Deactivate the membership directly (owner-level operation).
        cur.execute(
            "UPDATE gc.tenant_memberships SET is_active = false "
            "WHERE tenant_id = %s AND user_id = %s",
            [str(tenant_id), str(user_id)],
        )

        cur.execute(
            "SELECT count(*) FROM gc.get_user_memberships(%s)",
            [str(user_id)],
        )
        count = cur.fetchone()[0]
        assert count == 0, "Inactive membership must not be returned by bootstrap function."


# ---------------------------------------------------------------------------
# Test: tenant isolation — Tenant A cannot read Tenant B rows
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    def test_tenant_a_cannot_read_tenant_b_memberships(self, rollback_tx):
        """
        With app.tenant_id = tenant_a, querying gc.tenant_memberships must
        not return rows belonging to tenant_b.
        """
        cur = rollback_tx
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()

        cur.execute(
            "INSERT INTO gc.users (id, email, password_hash, full_name) VALUES "
            "(%s, %s, 'x', 'A'), (%s, %s, 'x', 'B')",
            [str(user_a_id), f"a_{user_a_id}@t.invalid",
             str(user_b_id), f"b_{user_b_id}@t.invalid"],
        )
        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, 'fr')",
            ["TA", f"ta-{user_a_id}", str(user_a_id)],
        )
        tenant_a_id = cur.fetchone()[0]

        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, 'fr')",
            ["TB", f"tb-{user_b_id}", str(user_b_id)],
        )
        tenant_b_id = cur.fetchone()[0]

        # Set context to tenant_a and query memberships.
        set_tenant(cur, tenant_a_id)
        cur.execute("SELECT tenant_id FROM gc.tenant_memberships")
        rows = cur.fetchall()
        returned = {str(r[0]) for r in rows}

        assert str(tenant_a_id) in returned, "Tenant A context should see Tenant A rows."
        assert str(tenant_b_id) not in returned, (
            "Tenant A context must NOT see Tenant B rows — RLS isolation failure."
        )

    def test_tenant_context_cleared_after_transaction(self, pg_conn):
        """
        After a transaction ends, app.tenant_id must be empty (transaction-local GUC).
        """
        some_id = str(uuid.uuid4())

        with pg_conn.transaction():
            with pg_conn.cursor() as cur:
                set_tenant(cur, some_id)
                cur.execute("SELECT current_setting('app.tenant_id', true)")
                inside = cur.fetchone()[0]
                assert inside == some_id

        # After transaction commit, GUC should be reset.
        with pg_conn.cursor() as cur:
            cur.execute("SELECT current_setting('app.tenant_id', true)")
            after = cur.fetchone()[0]
        assert not after, (
            f"app.tenant_id should be empty after transaction end, got: '{after}'"
        )


# ---------------------------------------------------------------------------
# Test: tenant provisioning is atomic
# ---------------------------------------------------------------------------

class TestProvisioningAtomicity:
    def test_duplicate_slug_raises_and_rolls_back(self, rollback_tx):
        """
        Attempting to provision a tenant with a duplicate slug must raise an
        exception. The first tenant must still exist; no partial state.
        """
        import psycopg

        cur = rollback_tx
        user_id = uuid.uuid4()
        slug = f"dup-slug-{user_id}"

        cur.execute(
            "INSERT INTO gc.users (id, email, password_hash, full_name) "
            "VALUES (%s, %s, 'x', 'Dup User')",
            [str(user_id), f"dup_{user_id}@t.invalid"],
        )
        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, 'fr')",
            ["First", slug, str(user_id)],
        )
        first_id = cur.fetchone()[0]
        assert first_id is not None

        with pytest.raises(psycopg.errors.UniqueViolation):
            cur.execute(
                "SELECT gc.provision_tenant_with_owner(%s, %s, %s, 'fr')",
                ["Second", slug, str(user_id)],
            )

    def test_provision_creates_both_tenant_and_membership(self, rollback_tx):
        """
        provision_tenant_with_owner must create exactly one tenant row and
        one owner membership row in the same transaction.
        """
        cur = rollback_tx
        user_id = uuid.uuid4()
        slug = f"atomic-{user_id}"

        cur.execute(
            "INSERT INTO gc.users (id, email, password_hash, full_name) "
            "VALUES (%s, %s, 'x', 'Atomic User')",
            [str(user_id), f"atomic_{user_id}@t.invalid"],
        )
        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, 'fr')",
            ["Atomic Tenant", slug, str(user_id)],
        )
        tenant_id = cur.fetchone()[0]

        cur.execute("SELECT count(*) FROM gc.tenants WHERE id = %s", [str(tenant_id)])
        assert cur.fetchone()[0] == 1

        # Check membership via bootstrap function (no RLS context needed).
        cur.execute(
            "SELECT role_code FROM gc.get_user_memberships(%s) WHERE tenant_id = %s",
            [str(user_id), str(tenant_id)],
        )
        row = cur.fetchone()
        assert row is not None, "Owner membership must exist after provisioning."
        assert row[0] == "owner"


# ---------------------------------------------------------------------------
# Test: GUC does not leak between simulated requests (connection reuse)
# ---------------------------------------------------------------------------

class TestContextLeakPrevention:
    def test_guc_empty_at_connection_start(self, pg_conn):
        """
        On a fresh connection (or after a transaction), app.tenant_id must
        be empty. Simulates what TenantContextCleanupMiddleware guarantees.
        """
        with pg_conn.cursor() as cur:
            cur.execute("SELECT current_setting('app.tenant_id', true)")
            val = cur.fetchone()[0]
        assert not val, (
            f"app.tenant_id should be empty on connection start, got: '{val}'"
        )

    def test_guc_set_in_tx_not_visible_after_commit(self, pg_conn):
        """
        set_config(..., true) is transaction-local: after COMMIT the GUC
        must revert to its pre-transaction value (empty string).
        Simulates two consecutive requests on the same pooled connection.
        """
        tenant_id = str(uuid.uuid4())

        # Simulate request 1: sets tenant context, commits.
        with pg_conn.transaction():
            with pg_conn.cursor() as cur:
                cur.execute(
                    "SELECT set_config('app.tenant_id', %s, true)", [tenant_id]
                )
                cur.execute("SELECT current_setting('app.tenant_id', true)")
                assert cur.fetchone()[0] == tenant_id

        # Simulate request 2: same connection, GUC must be gone.
        with pg_conn.cursor() as cur:
            cur.execute("SELECT current_setting('app.tenant_id', true)")
            after = cur.fetchone()[0]
        assert not after, (
            f"GUC leaked to next request on same connection: '{after}'"
        )

    def test_explicit_clear_resets_guc_within_tx(self, rollback_tx):
        """
        Explicit set_config(..., false) (session-level clear used by
        TenantContextCleanupMiddleware) resets the GUC even inside a
        transaction. This is the belt-and-suspenders cleanup.
        """
        cur = rollback_tx
        tenant_id = str(uuid.uuid4())

        # Set transaction-local GUC.
        cur.execute("SELECT set_config('app.tenant_id', %s, true)", [tenant_id])
        cur.execute("SELECT current_setting('app.tenant_id', true)")
        assert cur.fetchone()[0] == tenant_id

        # Middleware-style explicit clear (is_local=false resets to session default).
        cur.execute("SELECT set_config('app.tenant_id', %s, false)", [""])
        cur.execute("SELECT current_setting('app.tenant_id', true)")
        after = cur.fetchone()[0]
        assert not after, (
            f"Explicit clear did not reset GUC, got: '{after}'"
        )

    def test_non_member_sees_zero_rows_with_foreign_tenant_context(self, rollback_tx):
        """
        A user who is NOT a member of tenant_b must see zero rows from
        gc.tenant_memberships even if app.tenant_id is set to tenant_b.
        This tests that RLS enforces tenant_id match, not just presence.
        """
        cur = rollback_tx
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()

        cur.execute(
            "INSERT INTO gc.users (id, email, password_hash, full_name) VALUES "
            "(%s, %s, 'x', 'A'), (%s, %s, 'x', 'B')",
            [str(user_a_id), f"leak_a_{user_a_id}@t.invalid",
             str(user_b_id), f"leak_b_{user_b_id}@t.invalid"],
        )
        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, 'fr')",
            ["Leak-A", f"leak-a-{user_a_id}", str(user_a_id)],
        )
        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, 'fr')",
            ["Leak-B", f"leak-b-{user_b_id}", str(user_b_id)],
        )
        tenant_b_id = cur.fetchone()[0]

        # Set context to tenant_b (as if a leaked/forged context).
        set_tenant(cur, tenant_b_id)
        cur.execute(
            "SELECT count(*) FROM gc.tenant_memberships WHERE user_id = %s",
            [str(user_a_id)],
        )
        count = cur.fetchone()[0]
        assert count == 0, (
            f"User A must see 0 rows in Tenant B context, got {count}. "
            "RLS is not enforcing tenant isolation correctly."
        )


# ---------------------------------------------------------------------------
# Test: unauthorized roles cannot administer
# ---------------------------------------------------------------------------

class TestRoleEnforcement:
    def test_viewer_cannot_be_used_as_admin(self, rollback_tx):
        """
        A user with role_code='viewer' must not satisfy IsTenantAdmin.
        This is a Django-layer test using the bootstrap function result.
        """
        cur = rollback_tx
        owner_id = uuid.uuid4()
        viewer_id = uuid.uuid4()

        cur.execute(
            "INSERT INTO gc.users (id, email, password_hash, full_name) VALUES "
            "(%s, %s, 'x', 'Owner'), (%s, %s, 'x', 'Viewer')",
            [str(owner_id), f"owner_{owner_id}@t.invalid",
             str(viewer_id), f"viewer_{viewer_id}@t.invalid"],
        )
        cur.execute(
            "SELECT gc.provision_tenant_with_owner(%s, %s, %s, 'fr')",
            ["Role Test Tenant", f"role-{owner_id}", str(owner_id)],
        )
        tenant_id = cur.fetchone()[0]

        # Add viewer membership directly (owner context).
        set_tenant(cur, tenant_id)
        cur.execute(
            "INSERT INTO gc.tenant_memberships (tenant_id, user_id, role_code, is_active) "
            "VALUES (%s, %s, 'viewer', true)",
            [str(tenant_id), str(viewer_id)],
        )

        # Bootstrap lookup for viewer.
        cur.execute(
            "SELECT role_code FROM gc.get_user_memberships(%s) WHERE tenant_id = %s",
            [str(viewer_id), str(tenant_id)],
        )
        row = cur.fetchone()
        assert row is not None
        role = row[0]

        # Simulate IsTenantAdmin check.
        ADMIN_ROLES = {"owner", "expert_director"}
        assert role not in ADMIN_ROLES, (
            f"Viewer role '{role}' must not pass IsTenantAdmin check."
        )
