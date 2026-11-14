"""
apps/core/rls.py

Central tenant-context management for PostgreSQL RLS.

Design contract:
- app.tenant_id is set with set_config(..., true) — transaction-local only.
- The GUC is cleared automatically when the transaction ends (COMMIT/ROLLBACK).
- The caller is responsible for verifying active membership BEFORE calling
  activate_tenant_context(). This module does NOT verify membership itself.
- Platform-level operations (tenant creation, user lookup) must NOT call
  activate_tenant_context(); they run without a tenant GUC so RLS on
  platform tables (tenants, users) is not triggered.
- Never accept a tenant_id from client input without prior membership check.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

from django.db import connection, transaction

if TYPE_CHECKING:
    import uuid

logger = logging.getLogger(__name__)

# The GUC name must match current_tenant_id() in 001_initial_schema_v2.sql
_GUC = "app.tenant_id"


def _set_tenant_guc(tenant_id: str) -> None:
    """Execute SET LOCAL equivalent via set_config(..., true)."""
    with connection.cursor() as cur:
        cur.execute("SELECT set_config(%s, %s, true)", [_GUC, str(tenant_id)])


def _clear_tenant_guc() -> None:
    """Reset the GUC to empty string within the current transaction."""
    with connection.cursor() as cur:
        cur.execute("SELECT set_config(%s, %s, true)", [_GUC, ""])


def get_current_tenant_id() -> str | None:
    """
    Read the GUC value from the current transaction.
    Returns None if unset or empty — callers must treat None as 'no context'.
    """
    with connection.cursor() as cur:
        cur.execute("SELECT current_setting(%s, true)", [_GUC])
        row = cur.fetchone()
    value = row[0] if row else None
    return value if value else None


@contextmanager
def tenant_context(tenant_id: "uuid.UUID | str"):
    """
    Context manager that sets app.tenant_id for the duration of an atomic block.

    Usage (always inside an existing atomic block or wrapping one):

        with transaction.atomic():
            with tenant_context(tenant_id):
                # all ORM queries here see only this tenant's rows
                ...

    The GUC is transaction-local: PostgreSQL clears it on COMMIT/ROLLBACK.
    We also clear it explicitly on exit to guard against savepoint reuse
    within the same connection in a connection pool.

    Raises ValueError if tenant_id is falsy.
    """
    if not tenant_id:
        raise ValueError("tenant_context requires a non-empty tenant_id.")

    _set_tenant_guc(tenant_id)
    logger.debug("RLS context set: tenant_id=%s", tenant_id)
    try:
        yield
    finally:
        # Explicit clear is belt-and-suspenders: the transaction end already
        # resets transaction-local GUCs, but savepoints inside a larger
        # transaction do NOT reset them.
        _clear_tenant_guc()
        logger.debug("RLS context cleared: tenant_id=%s", tenant_id)


@contextmanager
def atomic_tenant_context(tenant_id: "uuid.UUID | str"):
    """
    Combines transaction.atomic() with tenant_context().

    This is the primary entry point for all tenant-scoped service calls.
    The GUC is set AFTER the savepoint/transaction is opened so it is
    always transaction-local.

    Example:
        with atomic_tenant_context(membership.tenant_id):
            result = some_service(...)
    """
    with transaction.atomic():
        with tenant_context(tenant_id):
            yield
