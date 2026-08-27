-- tenant_id scopes every row to one show: the real BrightKin/Everlight
-- Chronicles production data always uses the reserved sentinel
-- 'brightkin-canonical' (agents.tenant.BRIGHTKIN_TENANT_ID); a tester's
-- 'bring your own show' data uses a per-browser-session UUID instead. Every
-- read in agents/tools.py filters by tenant_id via a parameterized query, and
-- the intake endpoint (frontend/api/tenant-intake.py) refuses to write to the
-- reserved sentinel — so a tester's data can never leak into, or be confused
-- with, the canonical synthetic demo log. DEFAULT keeps existing callers (seed script,
-- write-path dashboard) working unchanged when they don't pass tenant_id.
CREATE TABLE IF NOT EXISTS production_events (
    item_id String,
    item_type String,
    stage String,
    status String,
    ts DateTime,
    notes String,
    tenant_id String DEFAULT 'brightkin-canonical'
) ENGINE = MergeTree()
ORDER BY (item_id, ts);

CREATE TABLE IF NOT EXISTS casting_and_assets (
    item_id String,
    character_or_track String,
    attribute_key String,
    attribute_value String,
    tenant_id String DEFAULT 'brightkin-canonical'
) ENGINE = MergeTree()
ORDER BY (item_id, character_or_track, attribute_key);

-- Shared per-IP request counter for /api/chat rate limiting. A Vercel Python
-- function is stateless per-invocation, so an in-memory counter would reset on
-- every cold start and wouldn't be shared across concurrent instances; this
-- table reuses the ClickHouse Cloud instance the app already depends on rather
-- than provisioning a separate Redis/Upstash account and secret just for
-- counting requests. TTL auto-expires rows after 1 day so the table stays small.
-- `id` exists purely so concurrent inserts for the same ip in the same second
-- form distinct data blocks: ClickHouse Cloud runs MergeTree as a replicated
-- engine under the hood and silently drops inserts whose block content
-- exactly matches a recent block (its automatic insert-deduplication) unless
-- there is some varying column to make each row unique.
CREATE TABLE IF NOT EXISTS rate_limit_events (
    ip String,
    ts DateTime DEFAULT now(),
    id UUID DEFAULT generateUUIDv4()
) ENGINE = MergeTree()
ORDER BY (ip, ts)
TTL ts + INTERVAL 1 DAY;
