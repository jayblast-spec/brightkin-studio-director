import importlib.util
import io
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_api_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "frontend" / "api" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _bare_handler(module, headers=None, body=b""):
    request = module.handler.__new__(module.handler)
    request.headers = headers or {}
    request.rfile = io.BytesIO(body)
    request.client_address = ("127.0.0.1", 1234)
    return request


def test_events_write_is_closed_when_admin_key_is_not_configured(monkeypatch):
    module = _load_api_module("events_api_no_key", "events.py")
    monkeypatch.delenv("EVENTS_ADMIN_KEY", raising=False)
    request = _bare_handler(module)
    responses = []
    request._send_json = lambda status, payload: responses.append((status, payload))

    request._handle_create()

    assert responses[0][0] == 503


def test_events_write_rejects_an_invalid_admin_key_before_database_access(monkeypatch):
    module = _load_api_module("events_api_bad_key", "events.py")
    monkeypatch.setenv("EVENTS_ADMIN_KEY", "correct-secret")
    monkeypatch.setattr(module, "get_client", lambda: pytest.fail("database must not be accessed"))
    request = _bare_handler(module, {"x-admin-key": "wrong-secret"})
    responses = []
    request._send_json = lambda status, payload: responses.append((status, payload))

    request._handle_create()

    assert responses[0][0] == 401


@pytest.mark.parametrize(
    ("module_name", "filename", "method_name", "headers"),
    [
        ("events_api_large", "events.py", "_handle_create", {"x-admin-key": "secret"}),
        ("chat_api_large", "chat.py", "_handle_chat", {}),
        ("intake_api_large", "tenant-intake.py", "_handle_create", {}),
    ],
)
def test_json_handlers_reject_oversized_bodies_before_reading(
    monkeypatch, module_name, filename, method_name, headers
):
    module = _load_api_module(module_name, filename)
    monkeypatch.setattr(module, "MAX_REQUEST_BODY_BYTES", 8)
    monkeypatch.setattr(module, "get_client", lambda: object())
    monkeypatch.setattr(module, "enforce_rate_limit", lambda *args, **kwargs: None)
    if filename == "events.py":
        monkeypatch.setenv("EVENTS_ADMIN_KEY", "secret")
    request = _bare_handler(module, {**headers, "Content-Length": "9"}, b"x" * 9)

    with pytest.raises(module.PayloadTooLargeError):
        getattr(request, method_name)()

    assert request.rfile.tell() == 0
