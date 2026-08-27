"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Clapperboard, Loader2, Plus, RefreshCcw } from "lucide-react";
import {
  listProductionItems,
  logProductionEvent,
  type NewProductionEvent,
  type ProductionItem,
} from "@/lib/production-client";
import { TiltCard } from "@/components/bk/TiltCard";

const ITEM_TYPES = ["track", "episode"];

const EMPTY_FORM: NewProductionEvent = {
  item_id: "",
  item_type: "track",
  stage: "",
  status: "",
  notes: "",
};

export function ProductionDashboard() {
  const [items, setItems] = useState<ProductionItem[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState<NewProductionEvent>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [justLogged, setJustLogged] = useState<string | null>(null);
  const [adminKey, setAdminKey] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    const result = await listProductionItems();
    if (result.ok) {
      setItems(result.items);
    } else {
      setLoadError(result.error);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    // Initial data fetch on mount, synchronizing this component with the
    // external ClickHouse-backed /api/events endpoint (not a state derived
    // from props/other state - the standard "fetch on mount" exception).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refresh();
  }, [refresh]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);
    setJustLogged(null);

    if (!adminKey.trim()) {
      setSubmitError("Admin key is required to write to the canonical production log.");
      return;
    }

    if (!form.item_id.trim() || !form.stage.trim() || !form.status.trim()) {
      setSubmitError("item_id, stage, and status are required.");
      return;
    }

    setSubmitting(true);
    const result = await logProductionEvent(form, adminKey);
    setSubmitting(false);

    if (!result.ok) {
      setSubmitError(result.error);
      return;
    }

    setJustLogged(result.event.item_id);
    setForm((f) => ({ ...EMPTY_FORM, item_type: f.item_type }));
    await refresh();
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[0.85fr_1.15fr]" style={{ perspective: "1600px" }}>
      <LogEventForm
        form={form}
        adminKey={adminKey}
        setAdminKey={setAdminKey}
        setForm={setForm}
        onSubmit={handleSubmit}
        submitting={submitting}
        submitError={submitError}
        justLogged={justLogged}
      />
      <ItemsTable items={items} loading={loading} loadError={loadError} onRefresh={refresh} />
    </div>
  );
}

function LogEventForm({
  form,
  adminKey,
  setAdminKey,
  setForm,
  onSubmit,
  submitting,
  submitError,
  justLogged,
}: {
  form: NewProductionEvent;
  adminKey: string;
  setAdminKey: (value: string) => void;
  setForm: React.Dispatch<React.SetStateAction<NewProductionEvent>>;
  onSubmit: (e: React.FormEvent) => void;
  submitting: boolean;
  submitError: string | null;
  justLogged: string | null;
}) {
  return (
    <TiltCard intensity={2.5} className="glass-panel grain rounded-3xl p-6">
      <div className="flex items-center gap-2">
        <Plus className="size-4 text-gold" aria-hidden />
        <h3 className="font-display text-lg font-semibold">Log a production event</h3>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        This performs a real <code className="font-mono text-gold-soft">INSERT</code> into{" "}
        <code className="font-mono text-gold-soft">production_events</code> - the same live
        ClickHouse table the Director and Compliance agents read from.
      </p>

      <form onSubmit={onSubmit} className="mt-6 space-y-4">
        <Field label="admin key" htmlFor="admin_key">
          <input
            id="admin_key"
            type="password"
            required
            autoComplete="off"
            value={adminKey}
            onChange={(e) => setAdminKey(e.target.value)}
            placeholder="Required for canonical writes"
            className="input-field"
          />
        </Field>

        <Field label="item_id" htmlFor="item_id">
          <input
            id="item_id"
            required
            value={form.item_id}
            onChange={(e) => setForm((f) => ({ ...f, item_id: e.target.value }))}
            placeholder="track_demo_horizon"
            className="input-field"
          />
        </Field>

        <Field label="item_type" htmlFor="item_type">
          <select
            id="item_type"
            value={form.item_type}
            onChange={(e) => setForm((f) => ({ ...f, item_type: e.target.value }))}
            className="input-field"
          >
            {ITEM_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </Field>

        <div className="grid grid-cols-2 gap-4">
          <Field label="stage" htmlFor="stage">
            <input
              id="stage"
              required
              value={form.stage}
              onChange={(e) => setForm((f) => ({ ...f, stage: e.target.value }))}
              placeholder="mixing"
              className="input-field"
            />
          </Field>
          <Field label="status" htmlFor="status">
            <input
              id="status"
              required
              value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              placeholder="in_progress"
              className="input-field"
            />
          </Field>
        </div>

        <Field label="notes (optional)" htmlFor="notes">
          <textarea
            id="notes"
            value={form.notes}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
            placeholder="Moved from distribution to mixing after final mix approval."
            rows={3}
            className="input-field resize-none"
          />
        </Field>

        {submitError && (
          <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {submitError}
          </p>
        )}

        {justLogged && !submitError && (
          <p className="inline-flex items-center gap-1.5 rounded-lg border border-success/30 bg-success/10 px-3 py-2 text-sm text-success">
            <CheckCircle2 className="size-4" aria-hidden />
            Logged a new event for <span className="font-mono">{justLogged}</span>.
          </p>
        )}

        <button
          type="submit"
          disabled={submitting}
          className="inline-flex w-full items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold text-primary-foreground transition-transform duration-150 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          style={{ backgroundImage: "var(--gradient-gold)" }}
        >
          {submitting ? (
            <>
              <Loader2 className="size-4 animate-spin" aria-hidden />
              Writing to ClickHouse…
            </>
          ) : (
            <>
              <Plus className="size-4" aria-hidden />
              Log event
            </>
          )}
        </button>
      </form>
    </TiltCard>
  );
}

function Field({ label, htmlFor, children }: { label: string; htmlFor: string; children: React.ReactNode }) {
  return (
    <div>
      <label htmlFor={htmlFor} className="mb-1.5 block font-mono text-[10px] tracking-[0.15em] text-muted-foreground uppercase">
        {label}
      </label>
      {children}
    </div>
  );
}

function ItemsTable({
  items,
  loading,
  loadError,
  onRefresh,
}: {
  items: ProductionItem[] | null;
  loading: boolean;
  loadError: string | null;
  onRefresh: () => void;
}) {
  return (
    <TiltCard intensity={2.5} className="glass-panel grain rounded-3xl p-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Clapperboard className="size-4 text-gold" aria-hidden />
          <h3 className="font-display text-lg font-semibold">Production items</h3>
        </div>
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--hairline)] bg-surface/50 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:border-gold/40 hover:text-foreground disabled:opacity-50"
        >
          <RefreshCcw className={loading ? "size-3.5 animate-spin" : "size-3.5"} aria-hidden />
          Refresh
        </button>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">
        Live <code className="font-mono text-gold-soft">SELECT</code> - each item shows its
        most-recently-logged stage and status.
      </p>

      <div className="mt-5 overflow-x-auto">
        {loadError && (
          <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {loadError}
          </p>
        )}

        {!loadError && items === null && (
          <p className="py-8 text-center text-sm text-muted-foreground">Loading production items…</p>
        )}

        {!loadError && items !== null && items.length === 0 && (
          <p className="py-8 text-center text-sm text-muted-foreground">No production events logged yet.</p>
        )}

        {!loadError && items !== null && items.length > 0 && (
          <table className="w-full min-w-[560px] border-collapse text-sm">
            <thead>
              <tr className="border-b border-[var(--hairline)] text-left">
                {["Item", "Type", "Stage", "Status", "Updated", "Notes"].map((h) => (
                  <th
                    key={h}
                    className="pb-2.5 pr-4 font-mono text-[10px] font-medium tracking-[0.14em] text-muted-foreground uppercase"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item, i) => (
                <tr
                  key={item.item_id}
                  className="row-3d row-in border-b border-[var(--hairline)]/60 last:border-0"
                  style={{ animationDelay: `${Math.min(i, 8) * 45}ms` }}
                >
                  <td className="py-2.5 pr-4 font-mono text-xs text-foreground">{item.item_id}</td>
                  <td className="py-2.5 pr-4 text-muted-foreground">{item.item_type}</td>
                  <td className="py-2.5 pr-4">{item.stage}</td>
                  <td className="py-2.5 pr-4">
                    <StatusPill status={item.status} />
                  </td>
                  <td className="py-2.5 pr-4 font-mono text-[11px] text-muted-foreground">
                    {formatTimestamp(item.last_update)}
                  </td>
                  <td className="py-2.5 pr-4 max-w-[220px] truncate text-muted-foreground" title={item.notes}>
                    {item.notes || "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </TiltCard>
  );
}

function StatusPill({ status }: { status: string }) {
  const isDone = status === "done" || status === "published";
  const isBlocked = status === "not_started" || status === "blocked";
  const tone = isDone ? "border-success/35 bg-success/10 text-success" : isBlocked
    ? "border-muted-foreground/25 bg-surface-raised text-muted-foreground"
    : "border-cyan/35 bg-cyan/10 text-cyan";
  return (
    <span className={`inline-flex items-center rounded-full border px-2 py-0.5 font-mono text-[11px] ${tone}`}>
      {status}
    </span>
  );
}

function formatTimestamp(value: string): string {
  const d = new Date(value.endsWith("Z") ? value : `${value}Z`);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}
