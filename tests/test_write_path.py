import pytest

from agents.tenant import BRIGHTKIN_TENANT_ID
from agents.tools import InvalidEventError, insert_production_event, list_latest_items


class FakeQueryResult:
    def __init__(self, column_names, rows):
        self.column_names = column_names
        self.result_rows = rows


class FakeClient:
    """Records exactly what insert()/query() were called with, so these tests
    can assert the write path uses the driver's parameter-binding insert API
    (never string-built SQL) without needing live ClickHouse credentials."""

    def __init__(self, latest_rows=None):
        self.inserted = []
        self.latest_rows = latest_rows or []

    def insert(self, table, data, column_names=None):
        self.inserted.append({"table": table, "data": data, "column_names": column_names})

    def query(self, sql, parameters=None):
        return FakeQueryResult(
            ["item_id", "item_type", "stage", "status", "notes", "last_update"],
            self.latest_rows,
        )


def test_insert_production_event_calls_insert_api_not_raw_sql():
    client = FakeClient()
    result = insert_production_event(
        client,
        item_id="track_we_are_brave",
        item_type="track",
        stage="mixing",
        status="in_progress",
        notes="moved from distribution",
    )
    assert len(client.inserted) == 1
    call = client.inserted[0]
    assert call["table"] == "production_events"
    assert call["column_names"] == ["item_id", "item_type", "stage", "status", "ts", "notes", "tenant_id"]
    row = call["data"][0]
    assert row[0] == "track_we_are_brave"
    assert row[2] == "mixing"
    assert row[3] == "in_progress"
    assert row[-1] == BRIGHTKIN_TENANT_ID
    assert result["item_id"] == "track_we_are_brave"
    assert result["stage"] == "mixing"
    assert result["tenant_id"] == BRIGHTKIN_TENANT_ID


def test_insert_production_event_scopes_to_supplied_tenant_id():
    client = FakeClient()
    result = insert_production_event(
        client, item_id="track_x", item_type="track", stage="mixing", status="in_progress",
        tenant_id="tester-abc",
    )
    row = client.inserted[0]["data"][0]
    assert row[-1] == "tester-abc"
    assert result["tenant_id"] == "tester-abc"


def test_insert_production_event_rejects_empty_item_id():
    client = FakeClient()
    with pytest.raises(InvalidEventError):
        insert_production_event(client, item_id="  ", item_type="track", stage="mixing", status="in_progress")
    assert client.inserted == []


def test_insert_production_event_rejects_oversized_field():
    client = FakeClient()
    with pytest.raises(InvalidEventError):
        insert_production_event(
            client, item_id="x" * 500, item_type="track", stage="mixing", status="in_progress"
        )
    assert client.inserted == []


def test_insert_production_event_rejects_oversized_notes():
    client = FakeClient()
    with pytest.raises(InvalidEventError):
        insert_production_event(
            client, item_id="track_x", item_type="track", stage="mixing", status="in_progress",
            notes="n" * 501,
        )
    assert client.inserted == []


def test_insert_production_event_defaults_missing_notes_to_empty_string():
    client = FakeClient()
    result = insert_production_event(
        client, item_id="track_x", item_type="track", stage="mixing", status="in_progress", notes=None
    )
    assert result["notes"] == ""


def test_list_latest_items_shapes_rows_as_dicts():
    client = FakeClient(
        latest_rows=[("track_x", "track", "mixing", "in_progress", "note", "2026-08-25T00:00:00")]
    )
    items = list_latest_items(client)
    assert items == [{
        "item_id": "track_x", "item_type": "track", "stage": "mixing",
        "status": "in_progress", "notes": "note", "last_update": "2026-08-25T00:00:00",
    }]
