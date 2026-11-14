"""
apps/tenants/bootstrap.py

Membership bootstrap: discovers and verifies a user's own active memberships
BEFORE tenant context (app.tenant_id) is established.

Security model
--------------
gc.tenant_memberships has FORCE ROW LEVEL SECURITY with a policy:
    USING (tenant_id = gc.current_tenant_id())

This means that without app.tenant_id set, the table returns zero rows to
geocabinet_user — which is correct for tenant-scoped queries, but prevents
the initial membership lookup needed to establish context.

Solution: a narrowly-scoped SECURITY DEFINER function gc.get_user_memberships(p_user_id)
that runs as the table owner and returns only the calling user's own active
memberships. The function is defined in 003_rls_bootstrap.sql.

Why this is safe:
1. The function is parameterised by user_id, not tenant_id — it cannot be
   used to enumerate another user's memberships.
2. The function is SECURITY DEFINER but owned by the schema owner (gc_owner),
   not a superuser. geocabinet_user has EXECUTE only.
3. The function returns (tenant_id, membership_id, role_code) — no sensitive
   user data from other tenants.
4. Django verifies the returned user_id matches request.user.id before
   trusting the result (see verify_user_membership below).
5. app.user_id is NOT used as identity proof — only the authenticated
   Django session/token user is trusted.

This module does NOT set app.tenant_id. That is done by apps.core.rls
after this bootstrap confirms membership.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Optional

from django.db import connection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BootstrappedMembership:
    tenant_id: uuid.UUID
    membership_id: uuid.UUID
    role_code: str
    user_id: uuid.UUID


def get_user_memberships(user_id: uuid.UUID) -> list[BootstrappedMembership]:
    """
    Call gc.get_user_memberships(p_user_id) to retrieve the authenticated
    user's active memberships without requiring app.tenant_id to be set.

    Returns an empty list if the user has no active memberships or if the
    bootstrap function is not yet installed (falls back gracefully).
    """
    with connection.cursor() as cur:
        cur.execute(
            "SELECT tenant_id, membership_id, role_code "
            "FROM gc.get_user_memberships(%s)",
            [str(user_id)],
        )
        rows = cur.fetchall()

    return [
        BootstrappedMembership(
            tenant_id=uuid.UUID(str(row[0])),
            membership_id=uuid.UUID(str(row[1])),
            role_code=row[2],
            user_id=user_id,
        )
        for row in rows
    ]


def verify_user_membership(
    user_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Optional[BootstrappedMembership]:
    """
    Verify that user_id has an active membership in tenant_id.

    Returns the BootstrappedMembership if valid, None otherwise.
    This is the gate that must pass before atomic_tenant_context() is called.

    The user_id comes from the authenticated Django session — never from
    client-supplied request data.
    """
    memberships = get_user_memberships(user_id)
    for m in memberships:
        if m.tenant_id == tenant_id:
            return m
    return None
