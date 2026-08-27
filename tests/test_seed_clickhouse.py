import os
import pytest
from agents.clickhouse_client import get_client
from scripts.seed_clickhouse import PRODUCTION_EVENTS, CASTING_AND_ASSETS


@pytest.mark.skipif(not os.environ.get("CLICKHOUSE_HOST"), reason="requires live ClickHouse credentials")
def test_seeded_row_counts_match():
    """Both tables are real append-only logs: production_events has had a
    write path since agents.tools.insert_production_event / POST /api/events,
    and casting_and_assets gained one too (agents.tools.insert_casting_attribute)
    for the 'bring your own show' intake endpoint (POST /api/tenant-intake),
    which writes tester-submitted diversity/camera-pacing attribute rows
    scoped to their own tenant_id. So this only asserts each table's seed
    floor is present, not an exact count - real activity (a tester's
    intake, or this repo's own live tenant-isolation tests) legitimately
    adds rows beyond the original seed for both tables now."""
    client = get_client()
    events_count = client.query("SELECT count() FROM production_events").result_rows[0][0]
    assets_count = client.query("SELECT count() FROM casting_and_assets").result_rows[0][0]
    assert events_count >= len(PRODUCTION_EVENTS)
    assert assets_count >= len(CASTING_AND_ASSETS)
