"""
GeoCabinet-DZ — Test Runner
============================

Two test suites:

1. SQLite smoke tests (this script)
   - Business logic: services, selectors, domain rules.
   - Uses SQLite in-memory + managed=True override.
   - Does NOT test RLS, PostgreSQL GUCs, or bootstrap functions.
   - Run: python run_tests.py

2. PostgreSQL / RLS integration tests (apps/tenants/tests_rls.py)
   - Tests RLS enforcement, bootstrap function isolation, tenant isolation,
     provisioning atomicity, and role enforcement.
   - Requires a dedicated PostgreSQL 15+ test database with the gc schema
     and bootstrap functions applied from 003_rls_bootstrap.sql.
   - Run: set GC_TEST_DB_NAME=geocabinet_test && python -m pytest apps/tenants/tests_rls.py -v
   - See apps/tenants/tests_rls.py for full setup instructions.

SQLite smoke tests are NOT proof of RLS correctness.
"""

import django
import sys
import unittest
from django.conf import settings

settings.configure(
    DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    INSTALLED_APPS=[
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "rest_framework",
        "apps.core",
        "apps.accounts",
        "apps.tenants",
    ],
    AUTH_USER_MODEL="accounts.CustomUser",
    SILENCED_SYSTEM_CHECKS=["auth.E003"],
    DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
    USE_TZ=True,
)
django.setup()

# Override managed=False so SQLite creates tables for testing.
# Production schema is owned by SQL v2.1; this is test-only.
# Also override db_table: SQLite does not support schema-qualified names (gc.*).
from apps.accounts.models import CustomUser
from apps.tenants.models import Tenant, TenantMembership, ProfessionalProfile

for model, table in [
    (CustomUser, "test_users"),
    (Tenant, "test_tenants"),
    (TenantMembership, "test_tenant_memberships"),
    (ProfessionalProfile, "test_professional_profiles"),
]:
    model._meta.managed = True
    model._meta.db_table = table

from django.test.utils import setup_test_environment
setup_test_environment()

from django.db import connection

with connection.schema_editor() as schema_editor:
    for model in [CustomUser, Tenant, TenantMembership, ProfessionalProfile]:
        schema_editor.create_model(model)

# ---------------------------------------------------------------------------
# Patch 1: selectors — bypass bootstrap DB function, use ORM directly.
# The bootstrap function (gc.get_user_memberships) is a PostgreSQL SECURITY
# DEFINER function not available in SQLite. Unit tests verify domain logic only.
# ---------------------------------------------------------------------------
import uuid as _uuid
import apps.tenants.selectors as _sel
from apps.tenants.models import Tenant as _Tenant, TenantMembership as _TM
from apps.tenants.bootstrap import BootstrappedMembership as _BM
from django.db import transaction as _tx
from django.core.exceptions import ValidationError as _VE


def _sqlite_get_user_tenants(user):
    return _Tenant.objects.filter(
        memberships__user=user,
        memberships__is_active=True,
    ).distinct()


def _sqlite_get_user_membership(user, tenant_id):
    row = _TM.objects.filter(
        user=user, tenant_id=tenant_id, is_active=True
    ).first()
    if not row:
        return None
    return _BM(
        tenant_id=_uuid.UUID(str(row.tenant_id)),
        membership_id=_uuid.UUID(str(row.id)),
        role_code=row.role_code,
        user_id=_uuid.UUID(str(user.id)),
    )


_sel.get_user_tenants = _sqlite_get_user_tenants
_sel.get_user_membership = _sqlite_get_user_membership

# ---------------------------------------------------------------------------
# Patch 2: services/core — bypass gc.provision_tenant_with_owner DB function.
# ---------------------------------------------------------------------------
import apps.tenants.services.core as _svc


@_tx.atomic
def _sqlite_create_tenant_with_owner(*, name, slug, user, default_locale="fr"):
    if _Tenant.objects.filter(slug=slug).exists():
        raise _VE(f"المكتب بالرمز '{slug}' موجود بالفعل.")
    tenant = _Tenant.objects.create(name=name, slug=slug, default_locale=default_locale)
    _TM.objects.create(tenant=tenant, user=user, role_code="owner", is_active=True)
    return tenant


_svc.create_tenant_with_owner = _sqlite_create_tenant_with_owner

# ---------------------------------------------------------------------------
# Patch 3: rls.atomic_tenant_context — no-op for SQLite (no GUC support).
# ---------------------------------------------------------------------------
import apps.core.rls as _rls
from contextlib import contextmanager as _cm


@_cm
def _noop_atomic_tenant_context(tenant_id):
    with _tx.atomic():
        yield


_rls.atomic_tenant_context = _noop_atomic_tenant_context

# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------
loader = unittest.TestLoader()
suite = loader.discover("apps/tenants", pattern="tests.py")
result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)

sys.exit(0 if result.wasSuccessful() else 1)
