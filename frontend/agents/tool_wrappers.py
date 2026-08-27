from agents.clickhouse_client import get_client
from agents.tenant import get_tenant
from agents.tools import (
    query_production_status,
    get_attributes,
    item_exists,
    debug_events_sql,
    debug_attributes_sql,
)
from agents.compliance import check_diversity, check_music_policy, check_pacing


def tool_query_status(item_id: str) -> dict:
    """Look up the production pipeline events for an episode or track by its item_id."""
    client = get_client()
    # tenant_id is NOT a parameter of this function: it's a per-request
    # routing decision (which show's data to answer against), read from the
    # contextvar frontend/api/chat.py sets before invoking the agent - never
    # something the Gemini model supplies as a tool argument.
    tenant_id = get_tenant()
    return {
        "item_id": item_id,
        "events": query_production_status(client, item_id, tenant_id=tenant_id),
        "sql": debug_events_sql(item_id, tenant_id=tenant_id),
    }


def _run_compliance_check(item_id: str, check_fn) -> dict:
    """Shared existence guard so a nonexistent item_id is reported as
    'no such item found' rather than silently reading as a compliance failure
    (an unknown item and a real failure both start from an empty attribute
    list, so they're indistinguishable unless checked explicitly)."""
    client = get_client()
    tenant_id = get_tenant()
    if not item_exists(client, item_id, tenant_id=tenant_id):
        return {"exists": False, "item_id": item_id, "sql": debug_attributes_sql(item_id, tenant_id=tenant_id)}
    result = check_fn(get_attributes(client, item_id, tenant_id=tenant_id))
    result["exists"] = True
    result["sql"] = debug_attributes_sql(item_id, tenant_id=tenant_id)
    return result


def tool_check_diversity(episode_id: str) -> dict:
    """Check whether an episode's cast meets BrightKin's diversity standard."""
    return _run_compliance_check(episode_id, check_diversity)


def tool_check_music_policy(track_id: str) -> dict:
    """Check whether a track meets BrightKin's original-music-only policy."""
    return _run_compliance_check(track_id, check_music_policy)


def tool_check_pacing(episode_id: str) -> dict:
    """Check whether an episode's scene sequence meets BrightKin's camera-variety standard."""
    return _run_compliance_check(episode_id, check_pacing)
