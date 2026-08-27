from agents.tenant import BRIGHTKIN_TENANT_ID
from agents.tools import query_production_status, get_attributes, item_exists, debug_events_sql, debug_attributes_sql


class FakeQueryResult:
    def __init__(self, column_names, rows):
        self.column_names = column_names
        self.result_rows = rows


class FakeClient:
    def __init__(self, rows_by_query):
        self.rows_by_query = rows_by_query
        self.last_call = None

    def query(self, sql, parameters=None):
        self.last_call = (sql, parameters)
        if "count()" in sql:
            return FakeQueryResult(["count()"], [(self.rows_by_query.get("count", 0),)])
        if "production_events" in sql:
            return FakeQueryResult(
                ["item_id", "item_type", "stage", "status", "ts", "notes"],
                self.rows_by_query.get("events", []),
            )
        return FakeQueryResult(
            ["item_id", "character_or_track", "attribute_key", "attribute_value"],
            self.rows_by_query.get("attrs", []),
        )


def test_query_production_status_shapes_rows_as_dicts():
    client = FakeClient({"events": [("episode_1", "episode", "script", "done", "2026-08-01", "note")]})
    result = query_production_status(client, "episode_1")
    assert result == [{
        "item_id": "episode_1", "item_type": "episode", "stage": "script",
        "status": "done", "ts": "2026-08-01", "notes": "note",
    }]
    assert client.last_call[1] == {"item_id": "episode_1", "tenant_id": BRIGHTKIN_TENANT_ID}


def test_get_attributes_shapes_rows_as_dicts():
    client = FakeClient({"attrs": [("episode_1", "Lumi", "voice_candidate", "Emmaline")]})
    result = get_attributes(client, "episode_1")
    assert result == [{
        "item_id": "episode_1", "character_or_track": "Lumi",
        "attribute_key": "voice_candidate", "attribute_value": "Emmaline",
    }]


def test_item_exists_true_when_count_positive():
    client = FakeClient({"count": 3})
    assert item_exists(client, "episode_1") is True


def test_item_exists_false_when_count_zero():
    client = FakeClient({"count": 0})
    assert item_exists(client, "no_such_item") is False


def test_debug_events_sql_is_escaped_and_never_executed():
    # Values that would break naive f-string interpolation (a single quote, and
    # a classic injection payload) must come back safely quoted, never inserted
    # raw - this string is display-only and is never passed to client.query().
    sql = debug_events_sql("ep' OR '1'='1")
    assert "ep\\' OR \\'1\\'=\\'1" in sql
    assert sql.count("'") % 2 == 0


def test_debug_attributes_sql_is_escaped_and_never_executed():
    sql = debug_attributes_sql("x'; DROP TABLE casting_and_assets; --")
    assert "DROP TABLE" in sql  # visible in the debug string...
    assert "x\\'; DROP TABLE" in sql  # ...but the quote is escaped, not a live delimiter


def test_debug_events_sql_also_escapes_tenant_id():
    sql = debug_events_sql("episode_1", tenant_id="t' OR '1'='1")
    assert "t\\' OR \\'1\\'=\\'1" in sql
    assert sql.count("'") % 2 == 0


def test_queries_scope_by_tenant_id_parameter():
    """Every read filters by tenant_id as a bound parameter (never string-built
    SQL) - same discipline as item_id."""
    client = FakeClient({"events": []})
    query_production_status(client, "episode_1", tenant_id="tester-abc")
    assert client.last_call[1] == {"item_id": "episode_1", "tenant_id": "tester-abc"}
    assert "{tenant_id:String}" in client.last_call[0]

    client = FakeClient({"attrs": []})
    get_attributes(client, "episode_1", tenant_id="tester-abc")
    assert client.last_call[1] == {"item_id": "episode_1", "tenant_id": "tester-abc"}
    assert "{tenant_id:String}" in client.last_call[0]
