# GeoCabinet DZ — ORM baseline v2.1

- `ERD_v2.1.mmd`: corrected logical ERD. Includes `mission_transitions` and missing B2B document/event relationships.
- `models.py`: Django ORM mapping for all 53 tables. All models are `managed = False`; the reviewed SQL remains schema authority.
- Composite tenant FKs, RLS, triggers, checks and partial indexes are intentionally not re-created as Django constraints.
- The ORM mapping is a first-pass bridge, not production-ready. In particular, validate ForeignKey mappings for composite FKs, use PostgreSQL ArrayField instead of JSONField for SQL arrays, and add explicit managers/services that set tenant context transaction-locally.
- Use a dedicated migration package with `RunSQL` for the database schema; do not let Django auto-create duplicate tables.

## Test boundary
The current execution container has no PostgreSQL/PostGIS server, `psql`, or Docker. Static consistency checks were run, but SQL execution, PostGIS behavior, and RLS runtime tests remain pending on a disposable PostgreSQL 15+PostGIS instance.
