/** 'Bring your own show' mode: a per-browser-session UUID identifies a
 * tester's own fictional-show data, generated once and cached in
 * localStorage (not a cookie - no server-side session needed, this is a
 * public, no-auth demo). The real BrightKin data is never reachable through
 * this id space: /api/tenant-intake rejects the reserved sentinel outright,
 * see agents/tenant.py.
 */

const STORAGE_KEY = "bk_tenant_id";

export function getOrCreateTenantId(): string {
  if (typeof window === "undefined") return "";
  try {
    const existing = window.localStorage.getItem(STORAGE_KEY);
    if (existing) return existing;
    const fresh = crypto.randomUUID();
    window.localStorage.setItem(STORAGE_KEY, fresh);
    return fresh;
  } catch {
    // Private browsing / storage blocked: fall back to a per-page-load id.
    // Intake and chat still work within this page view, just don't persist.
    return crypto.randomUUID();
  }
}

export type DistributionStatus = "not_started" | "in_review" | "distributed";
export type ProductionStatus = "not_started" | "in_progress" | "done";

export type TrackIntake = { title: string; distribution_status: DistributionStatus };

export type EpisodeIntake = {
  title: string;
  script_status: ProductionStatus;
  voice_casting_status: ProductionStatus;
  camera_pacing_varied: boolean;
  camera_pacing_note: string;
  cast_diversity_complete: boolean;
  cast_diversity_note: string;
};

type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string };

async function parseJsonOrError(res: Response): Promise<Record<string, unknown>> {
  try {
    return await res.json();
  } catch {
    return {};
  }
}

export async function checkTenantStatus(tenantId: string): Promise<ApiResult<{ hasData: boolean }>> {
  try {
    const res = await fetch(`/api/tenant-intake?tenant_id=${encodeURIComponent(tenantId)}`);
    const data = await parseJsonOrError(res);
    if (!res.ok || data.error) {
      return { ok: false, error: (data.error as string) ?? `Request failed (${res.status})` };
    }
    return { ok: true, data: { hasData: Boolean(data.has_data) } };
  } catch {
    return { ok: false, error: "Couldn't reach the production log." };
  }
}

export async function submitTenantIntake(
  tenantId: string,
  tracks: TrackIntake[],
  episode: EpisodeIntake
): Promise<ApiResult<{ episode_id: string }>> {
  try {
    const res = await fetch("/api/tenant-intake", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tenant_id: tenantId, tracks, episode }),
    });
    const data = await parseJsonOrError(res);
    if (!res.ok || data.error) {
      return { ok: false, error: (data.error as string) ?? `Request failed (${res.status})` };
    }
    return { ok: true, data: { episode_id: data.episode_id as string } };
  } catch {
    return { ok: false, error: "Couldn't reach the production log." };
  }
}
