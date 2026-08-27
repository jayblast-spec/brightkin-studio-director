"""Tenant scoping for 'bring your own show' mode.

The bundled canonical synthetic snapshot lives under a fixed sentinel tenant
id (BRIGHTKIN_TENANT_ID). A tester's own fictional-show data lives under a
per-browser-session UUID the frontend generates and sends on every request.
Every ClickHouse read/write in agents/tools.py is filtered by tenant_id via a
parameterized query, so a tester's tenant can never see (or, via the intake
endpoint, ever write into) the canonical BrightKin rows.

The active tenant for a request is threaded through as a contextvar rather
than as an extra parameter on the ADK tool functions themselves: ADK tools
are called by the Gemini model based on their Python signature, and the
tenant a question should be answered against is a server-side routing
decision, not something the model should be able to pick by supplying an
argument. frontend/api/chat.py sets this contextvar once per request before
invoking the agent runner; agents/tool_wrappers.py reads it internally.
"""

import contextvars
import re

# The real BrightKin/Everlight Chronicles production data. Reserved: no
# client-supplied tenant_id may ever equal this value (see
# normalize_new_tenant_id, used by the intake endpoint).
BRIGHTKIN_TENANT_ID = "brightkin-canonical"

_TENANT_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")

_current_tenant_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_tenant_id", default=BRIGHTKIN_TENANT_ID
)


class InvalidTenantError(ValueError):
    """A client-supplied tenant_id failed validation - a client error."""


def normalize_tenant_id(raw) -> str:
    """Validate a tenant_id used to *read* data (e.g. /api/chat's tenant_id
    field). Missing/blank normalizes to the canonical BrightKin tenant so
    existing callers that don't opt into 'bring your own show' are unaffected.
    Selecting the canonical id explicitly is allowed here - reading the real
    BrightKin data is the default, documented behavior, not a privilege
    escalation. Only *writing* to the canonical id is blocked
    (see normalize_new_tenant_id)."""
    if raw is None:
        return BRIGHTKIN_TENANT_ID
    if not isinstance(raw, str):
        raise InvalidTenantError("tenant_id must be a string")
    cleaned = raw.strip()
    if not cleaned:
        return BRIGHTKIN_TENANT_ID
    if not _TENANT_ID_RE.match(cleaned):
        raise InvalidTenantError(
            "tenant_id must be 1-64 characters of letters, digits, '-' or '_'"
        )
    return cleaned


def normalize_new_tenant_id(raw) -> str:
    """Validate a tenant_id used to *write* tester data via the intake
    endpoint. Unlike normalize_tenant_id, this rejects the reserved
    BRIGHTKIN_TENANT_ID sentinel outright - a tester's intake request can
    never target (and therefore can never modify or pollute) the real
    BrightKin production rows, no matter what tenant_id value is supplied."""
    if not isinstance(raw, str) or not raw.strip():
        raise InvalidTenantError("tenant_id is required")
    cleaned = raw.strip()
    if not _TENANT_ID_RE.match(cleaned):
        raise InvalidTenantError(
            "tenant_id must be 1-64 characters of letters, digits, '-' or '_'"
        )
    if cleaned == BRIGHTKIN_TENANT_ID:
        raise InvalidTenantError("tenant_id is reserved and cannot be used for intake")
    return cleaned


def set_tenant(tenant_id: str) -> contextvars.Token:
    """Set the active tenant for the current request; returns a token for
    reset_tenant. Call this once, near the top of the request handler."""
    return _current_tenant_id.set(tenant_id)


def reset_tenant(token: contextvars.Token) -> None:
    _current_tenant_id.reset(token)


def get_tenant() -> str:
    """The tenant the current request/tool call should be scoped to.
    Defaults to the canonical BrightKin tenant when no request has set one
    (e.g. direct unit-test calls, scripts)."""
    return _current_tenant_id.get()
