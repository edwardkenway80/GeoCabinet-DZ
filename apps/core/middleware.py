"""
apps/core/middleware.py

Clears the tenant RLS context after every response.

Why this is needed:
- Django's database connection pool reuses connections across requests.
- set_config(..., true) is transaction-local, so it is cleared on
  COMMIT/ROLLBACK. However, if a view exits without committing (e.g. during
  an unhandled exception that Django catches before the transaction ends),
  or if a connection is returned to the pool mid-transaction, the GUC could
  persist on the next request.
- This middleware is a safety net: it issues an explicit clear in a new
  autocommit-style cursor after the response is sent, ensuring the GUC
  is empty before the connection is reused.

This middleware must be placed AFTER Django's authentication middleware
so that request.user is available, but it does not depend on it.
"""

import logging

from django.db import connection

logger = logging.getLogger(__name__)

_GUC = "app.tenant_id"


class TenantContextCleanupMiddleware:
    """
    Clears app.tenant_id on the database connection after every response.
    Register in settings.MIDDLEWARE after SessionMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        self._clear_guc()
        return response

    def process_exception(self, request, exception):
        self._clear_guc()
        return None

    @staticmethod
    def _clear_guc() -> None:
        try:
            if connection.connection is not None:
                with connection.cursor() as cur:
                    cur.execute("SELECT set_config(%s, %s, false)", [_GUC, ""])
        except Exception:
            # Never let cleanup failure affect the response.
            logger.exception("Failed to clear tenant GUC after request.")
