import os
import pytest
from agents.clickhouse_client import get_client


@pytest.mark.skipif(not os.environ.get("CLICKHOUSE_HOST"), reason="requires live ClickHouse credentials")
def test_client_connects_and_can_query():
    client = get_client()
    result = client.query("SELECT 1")
    assert result.result_rows == [(1,)]
