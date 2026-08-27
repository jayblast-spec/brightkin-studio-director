import functools
import os
import socket
import time
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

# Network defaults: fail fast on a hung ClickHouse Cloud connection rather than
# letting a Vercel function invocation run out the clock silently.
CLICKHOUSE_CONNECT_TIMEOUT = float(os.environ.get("CLICKHOUSE_CONNECT_TIMEOUT", "10"))
CLICKHOUSE_SEND_RECEIVE_TIMEOUT = float(os.environ.get("CLICKHOUSE_SEND_RECEIVE_TIMEOUT", "30"))


def with_retry(retries: int = 1, backoff_seconds: float = 0.5, exceptions: tuple = (Exception,)):
    """Retry a flaky network call once (by default) with a short backoff.

    Kept deliberately simple: this project makes a handful of external calls per
    request (ClickHouse, Gemini) and only needs to smooth over transient network
    blips, not build a general resilience framework.
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(retries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:  # noqa: PERF203 - retry loop is intentional
                    last_exc = exc
                    if attempt < retries:
                        time.sleep(backoff_seconds * (attempt + 1))
            raise last_exc

        return wrapper

    return decorator

if os.environ.get("CLICKHOUSE_FORCE_PUBLIC_DNS") == "1":
    # Local-network workaround: this machine's default DNS resolver doesn't yet
    # have the ClickHouse Cloud service's freshly-provisioned record, even though
    # public resolvers (8.8.8.8) do. Not needed once local DNS catches up or in
    # any hosting environment with a normal resolver (e.g. Vercel).
    import dns.resolver

    _public_resolver = dns.resolver.Resolver(configure=False)
    _public_resolver.nameservers = ["8.8.8.8"]
    _original_getaddrinfo = socket.getaddrinfo

    def _patched_getaddrinfo(host, *args, **kwargs):
        try:
            return _original_getaddrinfo(host, *args, **kwargs)
        except socket.gaierror:
            answer = _public_resolver.resolve(host, "A")
            ip = str(answer[0])
            return _original_getaddrinfo(ip, *args, **kwargs)

    socket.getaddrinfo = _patched_getaddrinfo


@with_retry(retries=1, exceptions=(clickhouse_connect.driver.exceptions.Error, OSError, TimeoutError))
def get_client():
    return clickhouse_connect.get_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.environ.get("CLICKHOUSE_PORT", "8443")),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
        secure=True,
        connect_timeout=CLICKHOUSE_CONNECT_TIMEOUT,
        send_receive_timeout=CLICKHOUSE_SEND_RECEIVE_TIMEOUT,
    )
