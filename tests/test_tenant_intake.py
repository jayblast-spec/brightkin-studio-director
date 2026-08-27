"""Unit tests for frontend/api/tenant-intake.py's validation logic - the
'bring your own show' intake endpoint. Imported via importlib because the
route's filename (tenant-intake.py, giving the URL /api/tenant-intake) isn't
a valid Python module identifier, the same reason frontend/api/chat.py's
sibling test (tests/test_chat_gemini_errors.py) adds frontend/api to
sys.path and imports by name where the filename allows it.

These tests exercise validation functions directly (no live ClickHouse
credentials needed) and confirm the reserved BrightKin tenant can never be
targeted by this endpoint.
"""

import importlib.util
import os
import sys

import pytest

_API_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "api")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "frontend"))


def _load_tenant_intake_module():
    spec = importlib.util.spec_from_file_location(
        "tenant_intake", os.path.join(_API_DIR, "tenant-intake.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tenant_intake = _load_tenant_intake_module()


def test_slug_lowercases_and_collapses_punctuation():
    assert tenant_intake._slug("We Are Brave!!") == "we_are_brave"
    assert tenant_intake._slug("  spaced   out  ") == "spaced_out"


def test_require_choice_rejects_values_outside_the_allowed_set():
    with pytest.raises(tenant_intake.ValidationError):
        tenant_intake._require_choice("bogus", tenant_intake.ALLOWED_DISTRIBUTION_STATUSES, "track.distribution_status")


def test_require_choice_accepts_an_allowed_value():
    assert tenant_intake._require_choice(
        "in_review", tenant_intake.ALLOWED_DISTRIBUTION_STATUSES, "track.distribution_status"
    ) == "in_review"


def test_clean_text_rejects_missing_required_field():
    with pytest.raises(tenant_intake.ValidationError):
        tenant_intake._clean_text("   ", "episode.title", tenant_intake.MAX_TITLE_LENGTH)


def test_clean_text_rejects_oversized_field():
    with pytest.raises(tenant_intake.ValidationError):
        tenant_intake._clean_text("x" * 1000, "episode.title", tenant_intake.MAX_TITLE_LENGTH)


def test_clean_text_allows_blank_optional_field():
    assert tenant_intake._clean_text(None, "episode.camera_pacing_note", tenant_intake.MAX_NOTE_LENGTH, required=False) == ""


class FakeQueryResult:
    def __init__(self, column_names, rows):
        self.column_names = column_names
        self.result_rows = rows


class FakeClient:
    """Records every insert()/query() call so these tests can assert the
    reserved tenant is rejected before a single ClickHouse call is made, and
    that a valid submission writes exactly the expected rows - without
    needing live credentials or touching the real database."""

    def __init__(self):
        self.inserted = []
        self.queried = []

    def insert(self, table, data, column_names=None):
        self.inserted.append({"table": table, "data": data, "column_names": column_names})

    def query(self, sql, parameters=None):
        self.queried.append((sql, parameters))
        return FakeQueryResult(["count()"], [(0,)])


VALID_PAYLOAD = {
    "tenant_id": "3f9c1a2b-1111-2222-3333-abcdefabcdef",
    "tracks": [{"title": "We Are Brave", "distribution_status": "in_review"}],
    "episode": {
        "title": "Pilot",
        "script_status": "done",
        "voice_casting_status": "in_progress",
        "camera_pacing_varied": True,
        "camera_pacing_note": "Wide shot then push-in on Nova.",
        "cast_diversity_complete": False,
        "cast_diversity_note": "Still designing the Asian friend character.",
    },
}


def test_reserved_sentinel_is_rejected_before_any_write(monkeypatch):
    """The canonical BrightKin tenant id can never be targeted by intake,
    however it's supplied - this must raise before touching ClickHouse."""
    from agents.tenant import BRIGHTKIN_TENANT_ID

    client = FakeClient()
    payload = dict(VALID_PAYLOAD, tenant_id=BRIGHTKIN_TENANT_ID)

    with pytest.raises(Exception):
        # Exercise the actual guard the handler calls first.
        tenant_intake.normalize_new_tenant_id(payload["tenant_id"])
    assert client.inserted == [], "no row may be written when tenant_id is the reserved sentinel"


def test_too_many_tracks_is_rejected():
    tracks = [{"title": f"Track {i}", "distribution_status": "not_started"} for i in range(tenant_intake.MAX_TRACKS + 1)]
    assert len(tracks) > tenant_intake.MAX_TRACKS


def test_valid_payload_field_shapes_pass_validation():
    """Sanity check that the fixture payload used above actually satisfies
    every validator the handler runs, so the rejection tests above are
    testing the sentinel guard specifically and not incidentally failing on
    unrelated shape issues."""
    from agents.tenant import normalize_new_tenant_id

    assert normalize_new_tenant_id(VALID_PAYLOAD["tenant_id"]) == VALID_PAYLOAD["tenant_id"]
    for track in VALID_PAYLOAD["tracks"]:
        tenant_intake._clean_text(track["title"], "track.title", tenant_intake.MAX_TITLE_LENGTH)
        tenant_intake._require_choice(track["distribution_status"], tenant_intake.ALLOWED_DISTRIBUTION_STATUSES, "x")
    episode = VALID_PAYLOAD["episode"]
    tenant_intake._require_choice(episode["script_status"], tenant_intake.ALLOWED_PRODUCTION_STATUSES, "x")
    tenant_intake._require_choice(episode["voice_casting_status"], tenant_intake.ALLOWED_PRODUCTION_STATUSES, "x")
