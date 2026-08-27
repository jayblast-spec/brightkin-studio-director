"""Regression test for a real bug found under load: firing rapid sequential
requests at the live /api/chat produced a run of clean 200s, then a burst of
500s, before settling into clean 429s. Root cause (confirmed via `vercel
logs`): Gemini's own free-tier quota (429 RESOURCE_EXHAUSTED,
google.genai.errors.ClientError / google.adk's _ResourceExhaustedError
subclass) was falling through chat.py's typed exception handling into the
generic `except Exception -> 500` branch, and the retry wrapper was retrying
an instant-fail quota error pointlessly before giving up. This is not a
ClickHouse race condition - it happens even for a single caller once Gemini's
15-requests/minute free-tier limit is hit within a burst.
"""

import asyncio

import pytest
from google.genai.errors import ClientError as GeminiClientError

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "frontend", "api"))

import chat  # noqa: E402


def _make_quota_error(retry_delay: str = "35s") -> GeminiClientError:
    response_json = {
        "error": {
            "code": 429,
            "message": "You exceeded your current quota.",
            "status": "RESOURCE_EXHAUSTED",
            "details": [{"@type": "type.googleapis.com/google.rpc.RetryInfo", "retryDelay": retry_delay}],
        }
    }
    return GeminiClientError(429, response_json, None)


def test_gemini_retry_after_seconds_parses_retry_delay():
    exc = _make_quota_error("35s")
    assert chat._gemini_retry_after_seconds(exc) == 35


def test_gemini_retry_after_seconds_falls_back_when_missing():
    response_json = {"error": {"code": 429, "message": "quota", "status": "RESOURCE_EXHAUSTED", "details": []}}
    exc = GeminiClientError(429, response_json, None)
    assert chat._gemini_retry_after_seconds(exc) == 60


def test_run_debug_with_retry_does_not_retry_gemini_api_errors():
    """A GeminiAPIError must propagate immediately, not be swallowed into a
    pointless retry-then-500 - the caller needs it intact to map to a clean 429."""

    class FakeRunner:
        def __init__(self):
            self.calls = 0

        async def run_debug(self, question, quiet=True):
            self.calls += 1
            raise _make_quota_error()

    runner = FakeRunner()
    with pytest.raises(GeminiClientError):
        asyncio.run(chat._run_debug_with_retry(runner, "hello"))
    assert runner.calls == 1, "must not retry a Gemini API error (an instant retry cannot fix a quota wait)"


def test_run_debug_with_retry_still_retries_transient_errors():
    """Non-Gemini transient errors (e.g. a network blip) should still get the
    one retry."""

    class FlakyRunner:
        def __init__(self):
            self.calls = 0

        async def run_debug(self, question, quiet=True):
            self.calls += 1
            if self.calls == 1:
                raise ConnectionError("transient blip")
            return "ok"

    runner = FlakyRunner()
    result = asyncio.run(chat._run_debug_with_retry(runner, "hello", backoff_seconds=0.01))
    assert result == "ok"
    assert runner.calls == 2
