"""One-time, idempotent migration for the live ClickHouse Cloud instance:
adds the tenant_id column (see scripts/schema.sql) to the two tables that
already exist there, without touching any existing row's item_id/stage/
status/notes/attribute data.

Safe to run against a table that already has real BrightKin production rows:
- ADD COLUMN ... DEFAULT 'brightkin-canonical' IF NOT EXISTS is a metadata-only
  change plus a lazily-materialized default for existing rows - it does not
  rewrite the table's data parts, so it is cheap on the shared 30-day trial
  credit pool and carries no risk of altering/deleting existing rows.
- IF NOT EXISTS makes re-running this script a no-op if the column is already
  present, so it's safe to run again by mistake.

Run once after deploying the tenant-scoping code:
    python scripts/migrate_add_tenant_id.py
"""

from agents.clickhouse_client import get_client

_STATEMENTS = [
    "ALTER TABLE production_events ADD COLUMN IF NOT EXISTS tenant_id String DEFAULT 'brightkin-canonical'",
    "ALTER TABLE casting_and_assets ADD COLUMN IF NOT EXISTS tenant_id String DEFAULT 'brightkin-canonical'",
]


def migrate():
    client = get_client()
    for statement in _STATEMENTS:
        client.command(statement)
        print(f"OK: {statement}")


if __name__ == "__main__":
    migrate()
