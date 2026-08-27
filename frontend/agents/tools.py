from datetime import datetime, timezone

from clickhouse_connect.driver.binding import format_query_value

from agents.clickhouse_client import with_retry
from agents.tenant import BRIGHTKIN_TENANT_ID
from clickhouse_connect.driver.exceptions import Error as ClickHouseError

# Every query below is parameterized via clickhouse-connect's `{name:Type}`
# binding (client.query(sql, parameters={...})) - never f-string/str.format
# SQL text building. tenant_id is filtered the same way as item_id: as a bound
# parameter, never interpolated into the SQL string. This applies to both
# reads (WHERE tenant_id = {tenant_id:String}) and writes (an inserted
# column), so a tenant can never read or write another tenant's rows.
_EVENTS_SQL = (
    "SELECT item_id, item_type, stage, status, ts, notes FROM production_events "
    "WHERE item_id = {item_id:String} AND tenant_id = {tenant_id:String} ORDER BY ts"
)

_ATTRS_SQL = (
    "SELECT item_id, character_or_track, attribute_key, attribute_value FROM casting_and_assets "
    "WHERE item_id = {item_id:String} AND tenant_id = {tenant_id:String}"
)

_EXISTS_SQL = (
    "SELECT count() FROM casting_and_assets "
    "WHERE item_id = {item_id:String} AND tenant_id = {tenant_id:String}"
)

# One row per item_id, showing only its most-recently-logged stage/status -
# argMax(x, ts) picks the value of `x` from the row with the greatest `ts`,
# so a freshly INSERTed event (append-only MergeTree, never UPDATEd) becomes
# the row this returns for that item without needing any UPDATE/DELETE.
_LATEST_ITEMS_SQL = (
    "SELECT item_id, argMax(item_type, ts) AS item_type, argMax(stage, ts) AS stage, "
    "argMax(status, ts) AS status, argMax(notes, ts) AS notes, max(ts) AS last_update "
    "FROM production_events WHERE tenant_id = {tenant_id:String} "
    "GROUP BY item_id ORDER BY last_update DESC"
)

MAX_FIELD_LENGTH = 200
MAX_NOTES_LENGTH = 500
_REQUIRED_EVENT_FIELDS = ("item_id", "item_type", "stage", "status")


class InvalidEventError(ValueError):
    """A write-path input failed validation - a client error, not a backend failure."""


@with_retry(retries=1, exceptions=(ClickHouseError, OSError, TimeoutError))
def query_production_status(client, item_id: str, tenant_id: str = BRIGHTKIN_TENANT_ID) -> list[dict]:
    result = client.query(_EVENTS_SQL, parameters={"item_id": item_id, "tenant_id": tenant_id})
    return [dict(zip(result.column_names, row)) for row in result.result_rows]


@with_retry(retries=1, exceptions=(ClickHouseError, OSError, TimeoutError))
def get_attributes(client, item_id: str, tenant_id: str = BRIGHTKIN_TENANT_ID) -> list[dict]:
    result = client.query(_ATTRS_SQL, parameters={"item_id": item_id, "tenant_id": tenant_id})
    return [dict(zip(result.column_names, row)) for row in result.result_rows]


@with_retry(retries=1, exceptions=(ClickHouseError, OSError, TimeoutError))
def item_exists(client, item_id: str, tenant_id: str = BRIGHTKIN_TENANT_ID) -> bool:
    """Distinguish 'this item has no rows because it doesn't exist' from
    'this item exists but fails a compliance check' (an empty-attributes result
    looks identical to a real failure unless checked explicitly)."""
    result = client.query(_EXISTS_SQL, parameters={"item_id": item_id, "tenant_id": tenant_id})
    return bool(result.result_rows and result.result_rows[0][0] > 0)


def _validate_event_field(name: str, value, max_len: int = MAX_FIELD_LENGTH) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidEventError(f"'{name}' is required")
    cleaned = value.strip()
    if len(cleaned) > max_len:
        raise InvalidEventError(f"'{name}' must be {max_len} characters or fewer")
    return cleaned


@with_retry(retries=1, exceptions=(ClickHouseError, OSError, TimeoutError))
def list_latest_items(client, tenant_id: str = BRIGHTKIN_TENANT_ID) -> list[dict]:
    """Real dashboard read: one row per item_id with its current (most recent)
    stage/status, computed live from production_events - includes any item
    logged through the write path below, not just the original seed rows."""
    result = client.query(_LATEST_ITEMS_SQL, parameters={"tenant_id": tenant_id})
    rows = [dict(zip(result.column_names, row)) for row in result.result_rows]
    for row in rows:
        if hasattr(row["last_update"], "isoformat"):
            row["last_update"] = row["last_update"].isoformat()
    return rows


@with_retry(retries=1, exceptions=(ClickHouseError, OSError, TimeoutError))
def insert_production_event(
    client,
    item_id: str,
    item_type: str,
    stage: str,
    status: str,
    notes: str = "",
    tenant_id: str = BRIGHTKIN_TENANT_ID,
) -> dict:
    """Real write path: appends one row to production_events via
    clickhouse-connect's `client.insert`, which binds each column value as a
    driver-level parameter (the same non-string-interpolation path already
    used by scripts/seed_clickhouse.py and agents/rate_limit.py) rather than
    building any SQL text - there is no string to inject into.

    tenant_id defaults to the canonical BrightKin tenant so every existing
    caller (the write-path dashboard, the seed script) is unaffected; the
    'bring your own show' intake endpoint is the only caller that passes a
    tester's own tenant_id, and only after agents.tenant.normalize_new_tenant_id
    has rejected the reserved BrightKin sentinel."""
    item_id = _validate_event_field("item_id", item_id)
    item_type = _validate_event_field("item_type", item_type)
    stage = _validate_event_field("stage", stage)
    status = _validate_event_field("status", status)
    tenant_id = _validate_event_field("tenant_id", tenant_id, max_len=64)
    if notes is None:
        notes = ""
    if not isinstance(notes, str):
        raise InvalidEventError("'notes' must be a string")
    notes = notes.strip()
    if len(notes) > MAX_NOTES_LENGTH:
        raise InvalidEventError(f"'notes' must be {MAX_NOTES_LENGTH} characters or fewer")

    ts = datetime.now(timezone.utc).replace(tzinfo=None)
    client.insert(
        "production_events",
        [(item_id, item_type, stage, status, ts, notes, tenant_id)],
        column_names=["item_id", "item_type", "stage", "status", "ts", "notes", "tenant_id"],
    )
    return {
        "item_id": item_id,
        "item_type": item_type,
        "stage": stage,
        "status": status,
        "ts": ts.isoformat(),
        "notes": notes,
        "tenant_id": tenant_id,
    }


@with_retry(retries=1, exceptions=(ClickHouseError, OSError, TimeoutError))
def insert_casting_attribute(
    client,
    item_id: str,
    character_or_track: str,
    attribute_key: str,
    attribute_value: str,
    tenant_id: str = BRIGHTKIN_TENANT_ID,
) -> None:
    """Write path for casting_and_assets, used by the 'bring your own show'
    intake endpoint to record the structured attributes (cast-diversity
    designed/not_designed, camera_angle, provenance) the Compliance agent's
    checks (agents/compliance.py) actually read. Uses client.insert's
    parameter binding, same as insert_production_event above - never SQL
    string building."""
    item_id = _validate_event_field("item_id", item_id)
    character_or_track = _validate_event_field("character_or_track", character_or_track)
    attribute_key = _validate_event_field("attribute_key", attribute_key)
    attribute_value = _validate_event_field("attribute_value", attribute_value)
    tenant_id = _validate_event_field("tenant_id", tenant_id, max_len=64)
    client.insert(
        "casting_and_assets",
        [(item_id, character_or_track, attribute_key, attribute_value, tenant_id)],
        column_names=["item_id", "character_or_track", "attribute_key", "attribute_value", "tenant_id"],
    )


def debug_events_sql(item_id: str, tenant_id: str = BRIGHTKIN_TENANT_ID) -> str:
    """Display-only rendering of the parameterized events query for the UI's
    debug panel. Never executed - the real query above stays server-side
    parameterized via ClickHouse's `{name:Type}` binding. The value is escaped
    with clickhouse-connect's own literal formatter (the same code path the
    driver uses to render bind values), never raw string interpolation, so this
    cannot become a SQL-injection vector even though it looks like the query."""
    return (
        _EVENTS_SQL.replace("{item_id:String}", format_query_value(item_id))
        .replace("{tenant_id:String}", format_query_value(tenant_id))
    )


def debug_attributes_sql(item_id: str, tenant_id: str = BRIGHTKIN_TENANT_ID) -> str:
    return (
        _ATTRS_SQL.replace("{item_id:String}", format_query_value(item_id))
        .replace("{tenant_id:String}", format_query_value(tenant_id))
    )
