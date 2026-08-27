"""Per-IP request throttle for /api/chat.

Vercel Python functions are stateless per-invocation (no shared memory between
cold starts or concurrent instances), so an in-memory counter would not
actually limit anything in production. This uses the ClickHouse Cloud instance
the app already depends on as the shared counter store, instead of adding a
new Upstash/Redis account and secret purely to count requests.
"""

import uuid

from clickhouse_connect.driver.exceptions import Error as ClickHouseError

from agents.clickhouse_client import with_retry

DEFAULT_LIMIT = 20
DEFAULT_WINDOW_SECONDS = 3600

_COUNT_SQL = (
    "SELECT count() FROM rate_limit_events "
    "WHERE ip = {ip:String} AND ts > now() - INTERVAL {window:UInt32} SECOND"
)


class RateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded, retry after {retry_after_seconds}s")


@with_retry(retries=1, exceptions=(ClickHouseError, OSError, TimeoutError))
def _current_count(client, ip: str, window_seconds: int) -> int:
    result = client.query(_COUNT_SQL, parameters={"ip": ip, "window": window_seconds})
    return int(result.result_rows[0][0]) if result.result_rows else 0


@with_retry(retries=1, exceptions=(ClickHouseError, OSError, TimeoutError))
def _record(client, ip: str) -> None:
    # `id` is sent explicitly (not left to the column's server-side default):
    # ClickHouse Cloud runs MergeTree as a replicated engine and deduplicates
    # inserts by hashing the *transmitted* block, before server-side defaults
    # are applied - two inserts carrying only an identical `ip` value hash the
    # same and the second is silently dropped, undercounting real requests.
    client.insert("rate_limit_events", [(ip, str(uuid.uuid4()))], column_names=["ip", "id"])


def enforce_rate_limit(
    client,
    ip: str,
    limit: int = DEFAULT_LIMIT,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> None:
    """Raise RateLimitExceeded if `ip` has already made `limit` requests within
    `window_seconds`; otherwise record this request and return."""
    if _current_count(client, ip, window_seconds) >= limit:
        raise RateLimitExceeded(retry_after_seconds=window_seconds)
    _record(client, ip)
