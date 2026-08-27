import pytest

from agents.rate_limit import enforce_rate_limit, RateLimitExceeded


class FakeQueryResult:
    def __init__(self, rows):
        self.result_rows = rows


class FakeClient:
    """In-memory stand-in for the ClickHouse client, just enough surface for
    rate_limit.py's count()/insert() calls, so this test needs no live
    credentials and runs in every CI environment."""

    def __init__(self):
        self.rows = []

    def query(self, sql, parameters=None):
        count = sum(1 for ip in self.rows if ip == parameters["ip"])
        return FakeQueryResult([(count,)])

    def insert(self, table, data, column_names=None):
        for row in data:
            self.rows.append(row[0])


def test_allows_requests_under_the_limit():
    client = FakeClient()
    for _ in range(3):
        enforce_rate_limit(client, "1.2.3.4", limit=3, window_seconds=3600)


def test_blocks_the_request_that_exceeds_the_limit():
    client = FakeClient()
    for _ in range(3):
        enforce_rate_limit(client, "1.2.3.4", limit=3, window_seconds=3600)
    with pytest.raises(RateLimitExceeded) as exc_info:
        enforce_rate_limit(client, "1.2.3.4", limit=3, window_seconds=3600)
    assert exc_info.value.retry_after_seconds == 3600


def test_tracks_ips_independently():
    client = FakeClient()
    for _ in range(3):
        enforce_rate_limit(client, "1.1.1.1", limit=3, window_seconds=3600)
    # A different IP starts with its own fresh budget.
    enforce_rate_limit(client, "2.2.2.2", limit=3, window_seconds=3600)
