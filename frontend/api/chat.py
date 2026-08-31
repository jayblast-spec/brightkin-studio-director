import asyncio
import json
import logging
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler

# frontend/ is this function's project root; add it to sys.path so `agents` (the
# single source of truth also used by repo-root pytest via conftest.py) resolves
# without a hand-duplicated copy living in this directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickhouse_connect.driver.exceptions import Error as ClickHouseError
from google.adk.runners import InMemoryRunner
from google.genai.errors import APIError as GeminiAPIError

from agents.clickhouse_client import get_client
from agents.director_agent import director_agent
from agents.rate_limit import enforce_rate_limit, RateLimitExceeded
from agents.tenant import InvalidTenantError, normalize_tenant_id, reset_tenant, set_tenant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brightkin.chat")

RATE_LIMIT_PER_HOUR = int(os.environ.get("CHAT_RATE_LIMIT_PER_HOUR", "20"))
MAX_REQUEST_BODY_BYTES = int(os.environ.get("MAX_JSON_BODY_BYTES", "32768"))


class ValidationError(ValueError):
    """Bad or missing request input - a client error, not a backend failure."""


class PayloadTooLargeError(ValidationError):
    """The request body exceeds the configured JSON payload limit."""


def _gemini_retry_after_seconds(exc: GeminiAPIError) -> int:
    """Pull the server-suggested retry delay out of a 429's error details
    (details[...].retryDelay, e.g. '35s'); falls back to 60s if absent."""
    try:
        for item in exc.details.get("error", {}).get("details", []):
            delay = item.get("retryDelay")
            if delay:
                return max(1, int(float(str(delay).rstrip("s"))))
    except (AttributeError, TypeError, ValueError):
        pass
    return 60


async def _run_debug_with_retry(runner: InMemoryRunner, question: str, retries: int = 1, backoff_seconds: float = 0.5):
    """One retry with a short backoff around the Gemini/ADK call - enough to
    smooth over a transient upstream blip without masking a real failure.

    Deliberately does NOT retry a GeminiAPIError (400/403/429/5xx from the
    Gemini API itself): those are real upstream responses, not transient
    connection blips, and an immediate retry against a quota error the server
    just told us to wait 30+ seconds for cannot succeed - it only adds latency
    before the caller gets the same error. Let the caller map it straight to
    the right HTTP status (429 for quota, 502/503 for the rest) instead.
    """
    last_exc = None
    for attempt in range(retries + 1):
        try:
            return await runner.run_debug(question, quiet=True)
        except GeminiAPIError:
            raise
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                logger.warning("Gemini/ADK call failed (attempt %d), retrying: %s", attempt + 1, exc)
                await asyncio.sleep(backoff_seconds * (attempt + 1))
    raise last_exc


def _ask_director(question: str, tenant_id: str) -> dict:
    async def _run():
        runner = InMemoryRunner(agent=director_agent)
        events = await _run_debug_with_retry(runner, question)

        answer = "No response from the Director agent."
        final_author = "director_agent"
        delegated = False
        sql = None

        for event in events:
            if not event.content or not event.content.parts:
                continue
            for part in event.content.parts:
                if part.function_call and part.function_call.name == "transfer_to_agent":
                    delegated = True
                if part.function_response and isinstance(part.function_response.response, dict):
                    candidate_sql = part.function_response.response.get("sql")
                    if candidate_sql:
                        sql = candidate_sql
                if part.text:
                    answer = part.text
                    final_author = event.author

        if "compliance" in final_author:
            agent, specialist = "compliance", "Compliance"
        elif "greenlight" in final_author:
            agent, specialist = "greenlight", "Greenlight"
        elif "release" in final_author:
            agent, specialist = "release", "Release"
        else:
            agent, specialist = "director", "Director"
        route = f"Studio Mesh: Director → {specialist} specialist" if delegated else "Handled directly - production status lookup"
        return {"answer": answer, "agent": agent, "route": route, "query": sql}

    # Scope every tool call this agent run makes (director + any delegated
    # compliance sub-agent call) to `tenant_id` for the lifetime of this one
    # request, via the contextvar in agents/tenant.py - reset in `finally` so
    # a warm Vercel Python container never carries a tenant over into the
    # next unrelated request.
    token = set_tenant(tenant_id)
    try:
        return asyncio.run(_run())
    finally:
        reset_tenant(token)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            self._handle_chat()
        except PayloadTooLargeError as exc:
            self._send_json(413, {"error": str(exc)})
        except ValidationError as exc:
            logger.warning("Validation error on /api/chat: %s", exc)
            self._send_json(400, {"error": str(exc)})
        except RateLimitExceeded as exc:
            logger.info("Rate limit exceeded for /api/chat")
            self._send_429(
                exc.retry_after_seconds,
                f"Too many requests. Try again in {exc.retry_after_seconds // 60} minutes.",
            )
        except InvalidTenantError as exc:
            logger.warning("Invalid tenant_id on /api/chat: %s", exc)
            self._send_json(400, {"error": str(exc)})
        except GeminiAPIError as exc:
            logger.error("Gemini API error on /api/chat (code %s): %s", exc.code, traceback.format_exc())
            if exc.code == 429:
                retry_after = _gemini_retry_after_seconds(exc)
                self._send_429(retry_after, f"The AI model is temporarily busy. Try again in {retry_after} seconds.")
            else:
                self._send_json(502, {"error": "The AI model returned an error. Please retry shortly."})
        except ClickHouseError:
            logger.error("ClickHouse error on /api/chat: %s", traceback.format_exc())
            self._send_json(503, {"error": "Production log is temporarily unavailable. Please retry shortly."})
        except (OSError, TimeoutError):
            logger.error("Network/timeout error on /api/chat: %s", traceback.format_exc())
            self._send_json(503, {"error": "Upstream service timed out. Please retry shortly."})
        except Exception:
            logger.error("Unhandled error on /api/chat: %s", traceback.format_exc())
            self._send_json(500, {"error": "Something went wrong handling that request."})

    def _handle_chat(self):
        client_ip = self._client_ip()
        rate_client = get_client()
        enforce_rate_limit(rate_client, client_ip, limit=RATE_LIMIT_PER_HOUR)

        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError as exc:
            raise ValidationError("Content-Length must be an integer.") from exc
        if length < 0 or length > MAX_REQUEST_BODY_BYTES:
            raise PayloadTooLargeError(f"Request body must be {MAX_REQUEST_BODY_BYTES} bytes or fewer.")
        body = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ValidationError("Request body must be valid JSON.") from exc

        question = data.get("question", "").strip() if isinstance(data.get("question"), str) else ""
        if not question:
            raise ValidationError("Missing question")

        # tenant_id also accepted via an X-Tenant-Id header (the frontend
        # sends both); the body field wins if both are present. Missing/blank
        # normalizes to the canonical BrightKin tenant, so any caller that
        # predates 'bring your own show' keeps answering against the real
        # production data exactly as before.
        raw_tenant_id = data.get("tenant_id")
        if raw_tenant_id is None:
            raw_tenant_id = self.headers.get("x-tenant-id")
        tenant_id = normalize_tenant_id(raw_tenant_id)

        result = _ask_director(question, tenant_id)
        self._send_json(200, result)

    def _client_ip(self) -> str:
        forwarded = self.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = self.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        return self.client_address[0] if self.client_address else "unknown"

    def _send_429(self, retry_after_seconds: int, message: str):
        body = json.dumps({"error": message}).encode("utf-8")
        self.send_response(429)
        self.send_header("Content-Type", "application/json")
        self.send_header("Retry-After", str(retry_after_seconds))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
