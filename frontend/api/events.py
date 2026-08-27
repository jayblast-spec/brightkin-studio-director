import json
import hmac
import logging
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# frontend/ is this function's project root; add it to sys.path so `agents` (the
# single source of truth also used by repo-root pytest via conftest.py) resolves
# without a hand-duplicated copy living in this directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickhouse_connect.driver.exceptions import Error as ClickHouseError

from agents.clickhouse_client import get_client
from agents.rate_limit import enforce_rate_limit, RateLimitExceeded
from agents.tools import InvalidEventError, insert_production_event, list_latest_items

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brightkin.events")

# The dashboard GET is a single cheap SELECT (no Gemini call) so it gets a more
# generous budget than /api/chat's LLM-backed limit; the write POST reuses the
# same conservative default as chat to bound ClickHouse insert volume from any
# one caller.
READ_RATE_LIMIT_PER_HOUR = int(os.environ.get("EVENTS_READ_RATE_LIMIT_PER_HOUR", "120"))
WRITE_RATE_LIMIT_PER_HOUR = int(os.environ.get("EVENTS_WRITE_RATE_LIMIT_PER_HOUR", "20"))
MAX_REQUEST_BODY_BYTES = int(os.environ.get("MAX_JSON_BODY_BYTES", "32768"))


class ValidationError(ValueError):
    """Bad or missing request input - a client error, not a backend failure."""


class PayloadTooLargeError(ValidationError):
    """The request body exceeds the configured JSON payload limit."""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self._handle_list()
        except RateLimitExceeded as exc:
            logger.info("Rate limit exceeded for GET /api/events")
            self._send_429(exc.retry_after_seconds, f"Too many requests. Try again in {exc.retry_after_seconds // 60} minutes.")
        except ClickHouseError:
            logger.error("ClickHouse error on GET /api/events: %s", traceback.format_exc())
            self._send_json(503, {"error": "Production log is temporarily unavailable. Please retry shortly."})
        except (OSError, TimeoutError):
            logger.error("Network/timeout error on GET /api/events: %s", traceback.format_exc())
            self._send_json(503, {"error": "Upstream service timed out. Please retry shortly."})
        except Exception:
            logger.error("Unhandled error on GET /api/events: %s", traceback.format_exc())
            self._send_json(500, {"error": "Something went wrong handling that request."})

    def do_POST(self):
        try:
            self._handle_create()
        except PayloadTooLargeError as exc:
            self._send_json(413, {"error": str(exc)})
        except ValidationError as exc:
            logger.warning("Validation error on POST /api/events: %s", exc)
            self._send_json(400, {"error": str(exc)})
        except InvalidEventError as exc:
            logger.warning("Invalid event on POST /api/events: %s", exc)
            self._send_json(400, {"error": str(exc)})
        except RateLimitExceeded as exc:
            logger.info("Rate limit exceeded for POST /api/events")
            self._send_429(exc.retry_after_seconds, f"Too many requests. Try again in {exc.retry_after_seconds // 60} minutes.")
        except ClickHouseError:
            logger.error("ClickHouse error on POST /api/events: %s", traceback.format_exc())
            self._send_json(503, {"error": "Production log is temporarily unavailable. Please retry shortly."})
        except (OSError, TimeoutError):
            logger.error("Network/timeout error on POST /api/events: %s", traceback.format_exc())
            self._send_json(503, {"error": "Upstream service timed out. Please retry shortly."})
        except Exception:
            logger.error("Unhandled error on POST /api/events: %s", traceback.format_exc())
            self._send_json(500, {"error": "Something went wrong handling that request."})

    def _handle_list(self):
        client_ip = self._client_ip()
        client = get_client()
        enforce_rate_limit(client, client_ip, limit=READ_RATE_LIMIT_PER_HOUR)

        query = parse_qs(urlparse(self.path).query)
        limit = None
        if "limit" in query:
            try:
                limit = max(1, min(500, int(query["limit"][0])))
            except (ValueError, IndexError):
                raise ValidationError("'limit' must be an integer")

        items = list_latest_items(client)
        if limit is not None:
            items = items[:limit]
        self._send_json(200, {"items": items})

    def _handle_create(self):
        configured_key = os.environ.get("EVENTS_ADMIN_KEY", "")
        supplied_key = self.headers.get("x-admin-key", "")
        if not configured_key:
            self._send_json(503, {"error": "Canonical event writes are not configured."})
            return
        if not supplied_key or not hmac.compare_digest(supplied_key, configured_key):
            self._send_json(401, {"error": "A valid admin key is required to log canonical events."})
            return

        client_ip = self._client_ip()
        client = get_client()
        enforce_rate_limit(client, client_ip, limit=WRITE_RATE_LIMIT_PER_HOUR)

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

        if not isinstance(data, dict):
            raise ValidationError("Request body must be a JSON object.")

        event = insert_production_event(
            client,
            item_id=data.get("item_id", ""),
            item_type=data.get("item_type", ""),
            stage=data.get("stage", ""),
            status=data.get("status", ""),
            notes=data.get("notes", ""),
        )
        self._send_json(201, {"event": event})

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
