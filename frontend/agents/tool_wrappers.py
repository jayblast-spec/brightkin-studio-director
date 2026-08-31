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
from agents.mcp_evidence import run_mcp_query


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


def tool_assess_greenlight(item_id: str) -> dict:
    """Assess whether an item can advance from its current production stage."""
    client = get_client()
    tenant_id = get_tenant()
    events = query_production_status(client, item_id, tenant_id=tenant_id)
    if not events:
        return {"exists": False, "item_id": item_id, "decision": "NO_DATA", "sql": debug_events_sql(item_id, tenant_id)}
    latest = events[-1]
    blocking_words = ("blocked", "flagged", "failed", "hold", "incomplete")
    blockers = [latest] if any(
        word in f"{latest.get('status', '')} {latest.get('notes', '')}".lower()
        for word in blocking_words
    ) else []
    return {
        "exists": True,
        "item_id": item_id,
        "decision": "HOLD" if blockers else "GO",
        "current_stage": latest.get("stage"),
        "current_status": latest.get("status"),
        "blockers": blockers,
        "sql": debug_events_sql(item_id, tenant_id),
    }


def tool_assess_release(item_id: str) -> dict:
    """Combine production state and applicable standards into one release gate."""
    client = get_client()
    tenant_id = get_tenant()
    events = query_production_status(client, item_id, tenant_id=tenant_id)
    if not events:
        return {"exists": False, "item_id": item_id, "decision": "NO_DATA", "sql": debug_events_sql(item_id, tenant_id)}
    attributes = get_attributes(client, item_id, tenant_id=tenant_id)
    item_type = str(events[-1].get("item_type", "")).lower()
    checks = []
    if "track" in item_type:
        checks.append({"standard": "music_originality", **check_music_policy(attributes)})
    else:
        checks.extend([
            {"standard": "cast_diversity", **check_diversity(attributes)},
            {"standard": "camera_pacing", **check_pacing(attributes)},
        ])
    failed = [check for check in checks if not check.get("passed")]
    return {
        "exists": True,
        "item_id": item_id,
        "decision": "HOLD" if failed else "READY",
        "checks": checks,
        "gaps": failed,
        "sql": f"{debug_events_sql(item_id, tenant_id)}; {debug_attributes_sql(item_id, tenant_id)}",
    }


async def tool_mcp_release_evidence(item_id: str) -> dict:
    """Fetch release evidence via the official ClickHouse MCP server."""
    tenant_id = get_tenant()
    events_sql = debug_events_sql(item_id, tenant_id)
    attributes_sql = debug_attributes_sql(item_id, tenant_id)
    return {
        "item_id": item_id,
        "production_events": await run_mcp_query(events_sql),
        "standards_evidence": await run_mcp_query(attributes_sql),
        "sql": f"{events_sql}; {attributes_sql}",
        "transport": "official ClickHouse/mcp-clickhouse (in-memory MCP)",
    }
