"""'Bring your own show' intake: lets a hackathon judge/tester submit a
couple of facts about their own fictional show, scoped to a tenant_id their
browser generates itself (see frontend/lib/tenant-client.ts), so they can get
the same Director/Compliance agent experience grounded in their own data
instead of being limited to asking about the real BrightKin production data.

This never touches production_events/casting_and_assets rows belonging to
any other tenant, and can never write to the reserved BRIGHTKIN_TENANT_ID
sentinel - agents.tenant.normalize_new_tenant_id rejects that outright before
any query runs, and every insert below goes through agents.tools' insert
functions, which use clickhouse-connect's `client.insert`/parameterized
`client.query` (never f-string SQL).
"""

import json
import logging
import os
import sys
import traceback
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# frontend/ is this function's project root; add it to sys.path so `agents`
# resolves the same way the other /api/* functions in this repo do.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from clickhouse_connect.driver.exceptions import Error as ClickHouseError

from agents.clickhouse_client import get_client
from agents.rate_limit import enforce_rate_limit, RateLimitExceeded
from agents.tenant import InvalidTenantError, normalize_new_tenant_id, normalize_tenant_id
from agents.tools import (
    InvalidEventError,
    insert_casting_attribute,
    insert_production_event,
    list_latest_items,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("brightkin.tenant_intake")

READ_RATE_LIMIT_PER_HOUR = int(os.environ.get("TENANT_INTAKE_READ_RATE_LIMIT_PER_HOUR", "120"))
WRITE_RATE_LIMIT_PER_HOUR = int(os.environ.get("TENANT_INTAKE_WRITE_RATE_LIMIT_PER_HOUR", "10"))
MAX_REQUEST_BODY_BYTES = int(os.environ.get("MAX_JSON_BODY_BYTES", "32768"))

MAX_TRACKS = 2
MAX_TITLE_LENGTH = 120
MAX_NOTE_LENGTH = 300
ALLOWED_DISTRIBUTION_STATUSES = {"not_started", "in_review", "distributed"}
ALLOWED_PRODUCTION_STATUSES = {"not_started", "in_progress", "done"}
DIVERSITY_CHARACTERS = ("friend_char_white", "friend_char_latino", "friend_char_asian")


class ValidationError(ValueError):
    """Bad or missing request input - a client error, not a backend failure."""


class PayloadTooLargeError(ValidationError):
    """The request body exceeds the configured JSON payload limit."""


def _slug(title: str) -> str:
    cleaned = "".join(c.lower() if c.isalnum() else "_" for c in title.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")[:60] or "track"


def _require_choice(value, allowed: set[str], field: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise ValidationError(f"'{field}' must be one of: {', '.join(sorted(allowed))}")
    return value


def _clean_text(value, field: str, max_len: int, required: bool = True) -> str:
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be a string")
    cleaned = value.strip()
    if required and not cleaned:
        raise ValidationError(f"'{field}' is required")
    if len(cleaned) > max_len:
        raise ValidationError(f"'{field}' must be {max_len} characters or fewer")
    return cleaned


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            self._handle_status()
        except InvalidTenantError as exc:
            self._send_json(400, {"error": str(exc)})
        except RateLimitExceeded as exc:
            self._send_429(exc.retry_after_seconds, "Too many requests. Try again shortly.")
        except ClickHouseError:
            logger.error("ClickHouse error on GET /api/tenant-intake: %s", traceback.format_exc())
            self._send_json(503, {"error": "Production log is temporarily unavailable. Please retry shortly."})
        except (OSError, TimeoutError):
            self._send_json(503, {"error": "Upstream service timed out. Please retry shortly."})
        except Exception:
            logger.error("Unhandled error on GET /api/tenant-intake: %s", traceback.format_exc())
            self._send_json(500, {"error": "Something went wrong handling that request."})

    def do_POST(self):
        try:
            self._handle_create()
        except PayloadTooLargeError as exc:
            self._send_json(413, {"error": str(exc)})
        except (ValidationError, InvalidEventError, InvalidTenantError) as exc:
            logger.warning("Validation error on POST /api/tenant-intake: %s", exc)
            self._send_json(400, {"error": str(exc)})
        except RateLimitExceeded as exc:
            self._send_429(exc.retry_after_seconds, "Too many requests. Try again shortly.")
        except ClickHouseError:
            logger.error("ClickHouse error on POST /api/tenant-intake: %s", traceback.format_exc())
            self._send_json(503, {"error": "Production log is temporarily unavailable. Please retry shortly."})
        except (OSError, TimeoutError):
            self._send_json(503, {"error": "Upstream service timed out. Please retry shortly."})
        except Exception:
            logger.error("Unhandled error on POST /api/tenant-intake: %s", traceback.format_exc())
            self._send_json(500, {"error": "Something went wrong handling that request."})

    def _handle_status(self):
        """GET ?tenant_id=... - lets the frontend check whether this
        browser's tenant already has data, to decide whether to show the
        intake form or go straight to the chat."""
        client_ip = self._client_ip()
        client = get_client()
        enforce_rate_limit(client, client_ip, limit=READ_RATE_LIMIT_PER_HOUR)

        query = parse_qs(urlparse(self.path).query)
        raw_tenant_id = query.get("tenant_id", [None])[0]
        tenant_id = normalize_tenant_id(raw_tenant_id)
        items = list_latest_items(client, tenant_id=tenant_id)
        self._send_json(200, {"tenant_id": tenant_id, "has_data": len(items) > 0, "items": items})

    def _handle_create(self):
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

        # Reject/ignore any client-supplied tenant_id equal to the reserved
        # BrightKin sentinel (or anything else invalid) before touching
        # ClickHouse at all - the canonical snapshot rows are never reachable
        # through this endpoint.
        tenant_id = normalize_new_tenant_id(data.get("tenant_id"))

        tracks = data.get("tracks")
        if not isinstance(tracks, list) or not (1 <= len(tracks) <= MAX_TRACKS):
            raise ValidationError(f"'tracks' must be a list of 1-{MAX_TRACKS} items")

        episode = data.get("episode")
        if not isinstance(episode, dict):
            raise ValidationError("'episode' is required")

        created_items = []

        for raw_track in tracks:
            if not isinstance(raw_track, dict):
                raise ValidationError("each track must be an object")
            title = _clean_text(raw_track.get("title"), "track.title", MAX_TITLE_LENGTH)
            distribution_status = _require_choice(
                raw_track.get("distribution_status"), ALLOWED_DISTRIBUTION_STATUSES, "track.distribution_status"
            )
            item_id = f"{tenant_id}_track_{_slug(title)}"
            event = insert_production_event(
                client,
                item_id=item_id,
                item_type="track",
                stage="distribution",
                status=distribution_status,
                notes=f"Tester-submitted track: {title}",
                tenant_id=tenant_id,
            )
            created_items.append(event)

        episode_title = _clean_text(episode.get("title"), "episode.title", MAX_TITLE_LENGTH)
        script_status = _require_choice(episode.get("script_status"), ALLOWED_PRODUCTION_STATUSES, "episode.script_status")
        voice_casting_status = _require_choice(
            episode.get("voice_casting_status"), ALLOWED_PRODUCTION_STATUSES, "episode.voice_casting_status"
        )
        camera_pacing_varied = bool(episode.get("camera_pacing_varied"))
        camera_pacing_note = _clean_text(
            episode.get("camera_pacing_note"), "episode.camera_pacing_note", MAX_NOTE_LENGTH, required=False
        )
        cast_diversity_complete = bool(episode.get("cast_diversity_complete"))
        cast_diversity_note = _clean_text(
            episode.get("cast_diversity_note"), "episode.cast_diversity_note", MAX_NOTE_LENGTH, required=False
        )

        episode_id = f"{tenant_id}_episode_1"

        created_items.append(insert_production_event(
            client, item_id=episode_id, item_type="episode", stage="script",
            status=script_status, notes=f"Tester-submitted episode: {episode_title}", tenant_id=tenant_id,
        ))
        created_items.append(insert_production_event(
            client, item_id=episode_id, item_type="episode", stage="voice_casting",
            status=voice_casting_status, notes="", tenant_id=tenant_id,
        ))
        created_items.append(insert_production_event(
            client, item_id=episode_id, item_type="episode", stage="camera_pacing",
            status="varied" if camera_pacing_varied else "single_angle",
            notes=camera_pacing_note, tenant_id=tenant_id,
        ))
        created_items.append(insert_production_event(
            client, item_id=episode_id, item_type="episode", stage="cast_diversity",
            status="complete" if cast_diversity_complete else "incomplete",
            notes=cast_diversity_note, tenant_id=tenant_id,
        ))

        # Structured attributes the Compliance agent's checks (agents/compliance.py)
        # actually read - same shape as the seed data in scripts/seed_clickhouse.py,
        # just scoped to this tenant.
        for character in DIVERSITY_CHARACTERS:
            insert_casting_attribute(
                client, item_id=episode_id, character_or_track=character, attribute_key="status",
                attribute_value="designed" if cast_diversity_complete else "not_designed",
                tenant_id=tenant_id,
            )
        insert_casting_attribute(
            client, item_id=episode_id, character_or_track="scene_1", attribute_key="camera_angle",
            attribute_value="push-in", tenant_id=tenant_id,
        )
        insert_casting_attribute(
            client, item_id=episode_id, character_or_track="scene_2", attribute_key="camera_angle",
            attribute_value="wide" if camera_pacing_varied else "push-in", tenant_id=tenant_id,
        )

        self._send_json(201, {
            "tenant_id": tenant_id,
            "episode_id": episode_id,
            "track_ids": [item["item_id"] for item in created_items if item["item_type"] == "track"],
            "events_written": len(created_items),
        })

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
