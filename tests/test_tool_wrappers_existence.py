"""Fast, credential-free unit tests for the exists/fails distinction added to
the compliance tool wrappers. Complements the live-ClickHouse assertions in
test_tool_wrappers.py, which are skipped without CLICKHOUSE_HOST.
"""

from unittest.mock import MagicMock

import agents.tool_wrappers as tw


def test_tool_check_diversity_reports_missing_item(monkeypatch):
    monkeypatch.setattr(tw, "get_client", lambda: MagicMock())
    monkeypatch.setattr(tw, "item_exists", lambda client, item_id, tenant_id=None: False)
    result = tw.tool_check_diversity("no_such_episode")
    assert result["exists"] is False
    assert result["item_id"] == "no_such_episode"
    assert "passed" not in result


def test_tool_check_music_policy_reports_missing_item(monkeypatch):
    monkeypatch.setattr(tw, "get_client", lambda: MagicMock())
    monkeypatch.setattr(tw, "item_exists", lambda client, item_id, tenant_id=None: False)
    result = tw.tool_check_music_policy("no_such_track")
    assert result["exists"] is False
    assert "passed" not in result


def test_tool_check_pacing_reports_missing_item(monkeypatch):
    monkeypatch.setattr(tw, "get_client", lambda: MagicMock())
    monkeypatch.setattr(tw, "item_exists", lambda client, item_id, tenant_id=None: False)
    result = tw.tool_check_pacing("no_such_episode")
    assert result["exists"] is False


def test_tool_check_pacing_runs_normally_when_item_exists(monkeypatch):
    monkeypatch.setattr(tw, "get_client", lambda: MagicMock())
    monkeypatch.setattr(tw, "item_exists", lambda client, item_id, tenant_id=None: True)
    monkeypatch.setattr(
        tw,
        "get_attributes",
        lambda client, item_id, tenant_id=None: [
            {"attribute_key": "camera_angle", "attribute_value": "wide"},
            {"attribute_key": "camera_angle", "attribute_value": "push-in"},
        ],
    )
    result = tw.tool_check_pacing("episode_x")
    assert result["exists"] is True
    assert result["passed"] is True


def test_tool_check_diversity_still_fails_normally_when_item_exists(monkeypatch):
    monkeypatch.setattr(tw, "get_client", lambda: MagicMock())
    monkeypatch.setattr(tw, "item_exists", lambda client, item_id, tenant_id=None: True)
    monkeypatch.setattr(
        tw,
        "get_attributes",
        lambda client, item_id, tenant_id=None: [
            {"character_or_track": "friend_char_white", "attribute_key": "status", "attribute_value": "not_designed"},
        ],
    )
    result = tw.tool_check_diversity("episode_1")
    assert result["exists"] is True
    assert result["passed"] is False
    assert "friend_char_white" in result["missing"]
