# Migration Reliability Improvement Plan

Goal: Guarantee that every user – regardless of which historical version of JobManager they last ran or what tables they already have – can start the current version without seeing migration errors.

---

## 1. Catalogue the Current State
1.1 Inventory every migration file in `source/database/migrations/` and document the schema changes it performs.
1.2 Query several real-world databases from different user cohorts (very old, mid-way, almost-up-to-date) and record:
      • Existing tables/columns/indexes
      • Contents of `schema_migrations`
1.3 Identify drift situations, e.g. a table that exists but its migration filename is missing from `schema_migrations`.

## 2. Enforce Deterministic Migration Ordering
2.1 Rename all migration files to the canonical pattern `NNN_description.py` (they already mostly comply).
2.2 Replace the hard-coded list in `run_migration.py` with an automatic directory scan that:
      • Reads every `NNN_*.py` file in ascending numeric order.
      • Imports each module lazily with `importlib`.
      • Uses the filename (not module name) as the migration key stored in `schema_migrations`.
2.3 Keep the explicit mapping as a fallback for legacy names until step 7 (cleanup).

## 3. Make Every Migration Idempotent
3.1 Review each `migrate()` function; wrap every destructive/constructive statement with guards (`IF NOT EXISTS`, `DROP ... IF EXISTS`).
3.2 For model-based migrations that call `db.create_tables(models)`:
      • Ensure `safe=True` is passed or duplicate-table exceptions are handled.
3.3 Add unit-test style scripts (executed locally – never in user runtime) that run all migrations twice on an empty DB to confirm idempotency.

## 4. Introduce a “baseline” detector
4.1 Before applying pending migrations, run a quick introspection query to detect if the database already contains all objects created by a given migration while that migration is *not* listed in `schema_migrations`.
4.2 If true, **backfill** the missing row into `schema_migrations` and skip execution.
4.3 Ship this logic in `run_migration.apply_pending_migrations` right before the `pending_migrations` loop.

## 5. Strengthen Transaction & Error Handling
5.1 Keep the existing `with db.atomic():` block but wrap the whole migration loop in a larger savepoint; on any failure, rollback and abort further migrations.
5.2 Log the full traceback plus the SQL that failed.
5.3 Emit a user-friendly dialog instructing them to send the log file when an error surfaces.

## 6. Embed Migration Execution Early in Startup
6.1 Ensure `apply_pending_migrations()` is called from the very first bootstrap path (`source/bootstrap.py`) before any DAOs are instantiated.
6.2 Guard the call with a module-level flag so subsequent imports don’t re-run it.

## 7. Clean Up Legacy Artifacts (post-release)
7.1 After at least one stable release with the new system, delete the old hard-coded list logic.
7.2 Remove obsolete/mis-named migration files that are now impossible to hit.

## 8. Communicate to Users
8.1 Add a release-note section explaining that the application now self-repairs outdated databases.
8.2 Document manual recovery steps for extremely corrupt schemas (backup & fresh install).

## 9. Verification Checklist
✔ Fresh install → zero errors, all tables present.
✔ Database last updated at 001 → app starts, all later migrations apply.
✔ Database missing `schema_migrations` rows but tables exist → app backfills rows, no SQL attempted twice.
✔ Database fully up to date → no work performed.

---

Deliverables:
• Updated `run_migration.py` with automatic scanning, idempotent execution, baseline backfill, and improved logging.
• Revised individual migration files ensuring guards.
• Internal test script that migrates a throw-away database multiple times.
• Release notes entry.

