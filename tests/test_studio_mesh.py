from unittest.mock import Mock, patch

from agents.tenant import BRIGHTKIN_TENANT_ID
from agents.tool_wrappers import tool_assess_greenlight, tool_assess_release


@patch("agents.tool_wrappers.get_client")
@patch("agents.tool_wrappers.query_production_status")
def test_greenlight_uses_latest_event_not_resolved_history(query_status, get_client):
    get_client.return_value = Mock()
    query_status.return_value = [
        {"stage": "script", "status": "blocked", "notes": "missing draft"},
        {"stage": "voice", "status": "in_progress", "notes": "casting underway"},
    ]
    result = tool_assess_greenlight("episode_1")
    assert result["decision"] == "GO"
    assert result["current_stage"] == "voice"


@patch("agents.tool_wrappers.get_attributes", return_value=[])
@patch("agents.tool_wrappers.query_production_status")
@patch("agents.tool_wrappers.get_client", return_value=Mock())
def test_release_gate_returns_evidence_gaps(get_client, query_status, get_attributes):
    query_status.return_value = [{"item_type": "episode", "stage": "video", "status": "ready"}]
    result = tool_assess_release("episode_1")
    assert result["decision"] == "HOLD"
    assert {gap["standard"] for gap in result["gaps"]} == {"cast_diversity", "camera_pacing"}
    query_status.assert_called_once_with(get_client.return_value, "episode_1", tenant_id=BRIGHTKIN_TENANT_ID)
