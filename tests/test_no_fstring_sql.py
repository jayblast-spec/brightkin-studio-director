"""Static guard against a SQL-injection-shaped regression: every ClickHouse
query/insert in the new tenant-scoping code (agents/tools.py,
frontend/api/tenant-intake.py) must go through clickhouse-connect's
parameter binding (client.query(sql, parameters={...}) / client.insert(...))
rather than f-string/str.format-built SQL text. This repo already fixed one
SQL-injection-shaped dead-code finding earlier in the same style
(_events_sql/_attributes_sql in what's now agents/tools.py); this test keeps
that discipline from silently regressing as the tenant-scoping code grows.

The one intentional exception is the *_sql debug-display helpers
(debug_events_sql/debug_attributes_sql), which build a display-only string
using clickhouse_connect.driver.binding.format_query_value (the driver's own
literal-escaping formatter) - never executed, and explicitly covered by its
own escaping tests in tests/test_tools.py.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
FILES_TO_CHECK = [
    REPO_ROOT / "frontend" / "agents" / "tools.py",
    REPO_ROOT / "frontend" / "agents" / "rate_limit.py",
    REPO_ROOT / "frontend" / "api" / "tenant-intake.py",
    REPO_ROOT / "frontend" / "api" / "events.py",
    REPO_ROOT / "frontend" / "api" / "chat.py",
]

# An f-string or .format(...)/%-formatted string containing a SQL keyword is
# the shape of the bug we're guarding against: building the query text itself
# out of untrusted input instead of binding it as a parameter.
_SQL_KEYWORDS = r"(SELECT|INSERT|UPDATE|DELETE|ALTER|DROP|CREATE\s+TABLE)"
_FSTRING_SQL_RE = re.compile(rf"""f(['"]).*?\b{_SQL_KEYWORDS}\b""", re.IGNORECASE)
_PERCENT_SQL_RE = re.compile(rf"""(['"]).*?\b{_SQL_KEYWORDS}\b.*?\1\s*%\s*\(""", re.IGNORECASE)


def _violations(source: str) -> list[str]:
    violations = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if _FSTRING_SQL_RE.search(line) or _PERCENT_SQL_RE.search(line):
            violations.append(f"line {lineno}: {line.strip()}")
    return violations


def test_no_fstring_or_percent_built_sql_in_query_paths():
    all_violations = {}
    for path in FILES_TO_CHECK:
        source = path.read_text(encoding="utf-8")
        found = _violations(source)
        if found:
            all_violations[str(path)] = found
    assert not all_violations, f"f-string/percent-built SQL found: {all_violations}"


def test_every_client_query_call_passes_parameters_kwarg():
    """Every client.query(...) call site in the tenant-scoped tool layer must
    bind values via parameters=, not string-interpolate them into the SQL
    argument. debug_*_sql helpers are display-only and never call
    client.query, so they're outside this check by construction."""
    source = (REPO_ROOT / "frontend" / "agents" / "tools.py").read_text(encoding="utf-8")
    call_sites = re.findall(r"client\.query\([^)]*\)", source, re.DOTALL)
    assert call_sites, "expected at least one client.query(...) call site to check"
    for call in call_sites:
        assert "parameters=" in call, f"client.query call missing parameters=: {call}"
