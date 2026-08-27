import os
import pytest
from agents.tool_wrappers import (
    tool_query_status, tool_check_diversity, tool_check_music_policy, tool_check_pacing,
)

pytestmark = pytest.mark.skipif(not os.environ.get("CLICKHOUSE_HOST"), reason="requires live ClickHouse credentials")


def test_tool_query_status_returns_episode_1_events():
    result = tool_query_status("episode_1")
    assert result["item_id"] == "episode_1"
    assert any(e["stage"] == "script" and e["status"] == "done" for e in result["events"])


def test_tool_check_diversity_fails_for_episode_1():
    result = tool_check_diversity("episode_1")
    assert result["passed"] is False
    assert set(result["missing"]) == {"friend_char_white", "friend_char_latino", "friend_char_asian"}


def test_tool_check_music_policy_passes_for_seeded_track():
    result = tool_check_music_policy("track_we_are_the_future")
    assert result["passed"] is True


def test_tool_check_pacing_fails_for_episode_1():
    result = tool_check_pacing("episode_1")
    assert result["passed"] is False


def test_tool_check_diversity_reports_nonexistent_item_distinctly():
    """A made-up item_id must come back as 'not found', not as a compliance
    failure - both start from an empty attribute list, so this only works if
    tool_check_diversity checks existence first."""
    result = tool_check_diversity("no_such_item_ever_seeded_xyz")
    assert result["exists"] is False
    assert "passed" not in result
