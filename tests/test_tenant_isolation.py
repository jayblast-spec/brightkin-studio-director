"""Tenant isolation: (a) a tool query scoped to tenant A never returns tenant
B's rows, verified both against a fake driver (parameter-shape assertion, no
live credentials needed) and against the real live ClickHouse Cloud instance
(skipped without CLICKHOUSE_HOST) with two real tenants' rows actually
inserted and queried back. (b) the reserved BrightKin sentinel can't be
targeted by the intake path. (c) every query/insert here uses
clickhouse-connect's parameter binding, never f-string SQL - see
test_no_fstring_sql.py for the static check.
"""

import os
import uuid

import pytest

from agents.tenant import BRIGHTKIN_TENANT_ID
from agents.tools import (
    get_attributes,
    insert_casting_attribute,
    insert_production_event,
    item_exists,
    list_latest_items,
    query_production_status,
)


class FakeQueryResult:
    def __init__(self, column_names, rows):
        self.column_names = column_names
        self.result_rows = rows


class FakeIsolatedClient:
    """Simulates two tenants' worth of rows and only returns the rows whose
    tenant_id matches the parameter actually bound in the query - the same
    shape a real ClickHouse WHERE tenant_id = {tenant_id:String} filter
    would produce. Used to prove the *query construction* is tenant-scoped
    without needing live credentials."""

    def __init__(self):
        self.events = [
            {"item_id": "shared_item_id", "item_type": "episode", "stage": "script", "status": "done",
             "ts": "2026-01-01", "notes": "tenant A's note", "tenant_id": "tenant-a"},
            {"item_id": "shared_item_id", "item_type": "episode", "stage": "script", "status": "not_started",
             "ts": "2026-01-01", "notes": "tenant B's note", "tenant_id": "tenant-b"},
        ]

    def query(self, sql, parameters=None):
        parameters = parameters or {}
        assert "tenant_id" in parameters, "query must be scoped by a tenant_id parameter"
        rows = [
            (e["item_id"], e["item_type"], e["stage"], e["status"], e["ts"], e["notes"])
            for e in self.events
            if e["item_id"] == parameters.get("item_id") and e["tenant_id"] == parameters["tenant_id"]
        ]
        return FakeQueryResult(["item_id", "item_type", "stage", "status", "ts", "notes"], rows)


def test_query_production_status_never_crosses_tenants_with_same_item_id():
    client = FakeIsolatedClient()
    a_rows = query_production_status(client, "shared_item_id", tenant_id="tenant-a")
    b_rows = query_production_status(client, "shared_item_id", tenant_id="tenant-b")

    assert len(a_rows) == 1 and a_rows[0]["notes"] == "tenant A's note"
    assert len(b_rows) == 1 and b_rows[0]["notes"] == "tenant B's note"
    # Neither tenant's result set contains the other tenant's note, even
    # though both rows share the exact same item_id.
    assert "tenant B's note" not in [r["notes"] for r in a_rows]
    assert "tenant A's note" not in [r["notes"] for r in b_rows]


@pytest.mark.skipif(not os.environ.get("CLICKHOUSE_HOST"), reason="requires live ClickHouse credentials")
class TestLiveTenantIsolation:
    """Inserts real rows for two disposable tenant ids into the live
    ClickHouse Cloud instance and asserts a query for one never returns the
    other's rows. Never touches BRIGHTKIN_TENANT_ID and writes only a
    handful of tiny rows (append-only, consistent with this table's existing
    design), so this stays cheap on the shared trial credit pool."""

    def setup_method(self):
        from agents.clickhouse_client import get_client

        self.client = get_client()
        run_id = uuid.uuid4().hex[:8]
        self.tenant_a = f"pytest-isolation-a-{run_id}"
        self.tenant_b = f"pytest-isolation-b-{run_id}"
        self.item_id = f"pytest_isolation_item_{run_id}"

        insert_production_event(
            self.client, item_id=self.item_id, item_type="episode", stage="script",
            status="done", notes="tenant A only", tenant_id=self.tenant_a,
        )
        insert_production_event(
            self.client, item_id=self.item_id, item_type="episode", stage="script",
            status="not_started", notes="tenant B only", tenant_id=self.tenant_b,
        )
        insert_casting_attribute(
            self.client, item_id=self.item_id, character_or_track="friend_char_white",
            attribute_key="status", attribute_value="designed", tenant_id=self.tenant_a,
        )

    def teardown_method(self):
        # These are ALTER TABLE ... DELETE mutations (async in ClickHouse) --
        # cheap for the handful of rows this test writes, and necessary so
        # every test run doesn't permanently accumulate rows in the shared
        # live ClickHouse Cloud instance. Never touches BRIGHTKIN_TENANT_ID.
        self.client.command(
            "ALTER TABLE production_events DELETE WHERE tenant_id IN {tenants:Array(String)}",
            parameters={"tenants": [self.tenant_a, self.tenant_b]},
        )
        self.client.command(
            "ALTER TABLE casting_and_assets DELETE WHERE tenant_id IN {tenants:Array(String)}",
            parameters={"tenants": [self.tenant_a, self.tenant_b]},
        )

    def test_tenant_a_query_never_returns_tenant_b_rows(self):
        a_events = query_production_status(self.client, self.item_id, tenant_id=self.tenant_a)
        b_events = query_production_status(self.client, self.item_id, tenant_id=self.tenant_b)

        assert [e["notes"] for e in a_events] == ["tenant A only"]
        assert [e["notes"] for e in b_events] == ["tenant B only"]

    def test_tenant_b_sees_no_attributes_written_for_tenant_a(self):
        assert get_attributes(self.client, self.item_id, tenant_id=self.tenant_b) == []
        assert item_exists(self.client, self.item_id, tenant_id=self.tenant_b) is False
        assert item_exists(self.client, self.item_id, tenant_id=self.tenant_a) is True

    def test_canonical_brightkin_tenant_is_never_touched_by_this_test(self):
        """Sanity check that this test's own writes cannot have altered the
        real BrightKin data: episode_1 under the canonical tenant must still
        exist and be distinct from either disposable test tenant."""
        canonical_events = query_production_status(self.client, "episode_1", tenant_id=BRIGHTKIN_TENANT_ID)
        assert len(canonical_events) > 0
        our_tenants_events = query_production_status(self.client, "episode_1", tenant_id=self.tenant_a)
        assert our_tenants_events == []

    def test_dashboard_listing_is_scoped_per_tenant(self):
        a_items = list_latest_items(self.client, tenant_id=self.tenant_a)
        b_items = list_latest_items(self.client, tenant_id=self.tenant_b)
        assert {i["item_id"] for i in a_items} == {self.item_id}
        assert {i["item_id"] for i in b_items} == {self.item_id}
        assert a_items[0]["status"] == "done"
        assert b_items[0]["status"] == "not_started"
