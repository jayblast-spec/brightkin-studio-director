export type ProductionItem = {
  item_id: string;
  item_type: string;
  stage: string;
  status: string;
  notes: string;
  last_update: string;
};

export type NewProductionEvent = {
  item_id: string;
  item_type: string;
  stage: string;
  status: string;
  notes?: string;
};

export type ProductionClientError = { error: string };

async function parseJsonOrError(res: Response): Promise<Record<string, unknown>> {
  try {
    return await res.json();
  } catch {
    return {};
  }
}

/** Real GET against /api/events, backed by a live SELECT over production_events. */
export async function listProductionItems(): Promise<
  { ok: true; items: ProductionItem[] } | { ok: false; error: string }
> {
  try {
    const res = await fetch("/api/events", { method: "GET" });
    const data = await parseJsonOrError(res);
    if (!res.ok || data.error) {
      return { ok: false, error: (data.error as string) ?? `Request failed (${res.status})` };
    }
    return { ok: true, items: (data.items as ProductionItem[]) ?? [] };
  } catch {
    return { ok: false, error: "Couldn't reach the production log." };
  }
}

/** Real POST against /api/events - performs a real INSERT into production_events. */
export async function logProductionEvent(
  event: NewProductionEvent,
  adminKey: string
): Promise<{ ok: true; event: ProductionItem } | { ok: false; error: string }> {
  try {
    const res = await fetch("/api/events", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Admin-Key": adminKey },
      body: JSON.stringify(event),
    });
    const data = await parseJsonOrError(res);
    if (!res.ok || data.error) {
      return { ok: false, error: (data.error as string) ?? `Request failed (${res.status})` };
    }
    return { ok: true, event: data.event as ProductionItem };
  } catch {
    return { ok: false, error: "Couldn't reach the production log." };
  }
}
