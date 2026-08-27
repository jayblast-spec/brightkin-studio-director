"use client";

import { useState } from "react";
import { Clapperboard, Loader2, Sparkles } from "lucide-react";
import {
  submitTenantIntake,
  type DistributionStatus,
  type EpisodeIntake,
  type ProductionStatus,
  type TrackIntake,
} from "@/lib/tenant-client";

const EMPTY_TRACK: TrackIntake = { title: "", distribution_status: "not_started" };

const EMPTY_EPISODE: EpisodeIntake = {
  title: "",
  script_status: "not_started",
  voice_casting_status: "not_started",
  camera_pacing_varied: false,
  camera_pacing_note: "",
  cast_diversity_complete: false,
  cast_diversity_note: "",
};

export function TenantIntakeForm({
  tenantId,
  onSubmitted,
}: {
  tenantId: string;
  onSubmitted: () => void;
}) {
  const [tracks, setTracks] = useState<TrackIntake[]>([EMPTY_TRACK]);
  const [episode, setEpisode] = useState<EpisodeIntake>(EMPTY_EPISODE);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function updateTrack(i: number, patch: Partial<TrackIntake>) {
    setTracks((t) => t.map((track, idx) => (idx === i ? { ...track, ...patch } : track)));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const cleanTracks = tracks.filter((t) => t.title.trim());
    if (cleanTracks.length === 0) {
      setError("Add at least one track title.");
      return;
    }
    if (!episode.title.trim()) {
      setError("Give your episode a title.");
      return;
    }

    setSubmitting(true);
    const result = await submitTenantIntake(tenantId, cleanTracks, episode);
    setSubmitting(false);

    if (!result.ok) {
      setError(result.error);
      return;
    }
    onSubmitted();
  }

  return (
    <div className="glass-panel grain relative overflow-hidden rounded-3xl p-6">
      <div className="flex items-center gap-2">
        <Sparkles className="size-4 text-gold" aria-hidden />
        <h3 className="font-display text-lg font-semibold">Tell us about your show</h3>
      </div>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        A few facts about your own fictional show. This performs a real{" "}
        <code className="font-mono text-gold-soft">INSERT</code> into ClickHouse, scoped to a
        private id your browser just generated - it can never see or affect BrightKin&apos;s real
        production data, and no other tester can see yours.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-6">
        <fieldset className="space-y-4">
          <legend className="font-mono text-[10px] tracking-[0.15em] text-muted-foreground uppercase">
            Track{tracks.length > 1 ? "s" : ""} (up to 2)
          </legend>
          {tracks.map((track, i) => (
            <div key={i} className="grid grid-cols-[1fr_auto] gap-3">
              <input
                value={track.title}
                onChange={(e) => updateTrack(i, { title: e.target.value })}
                placeholder={i === 0 ? "e.g. We Rise Together" : "second track title (optional)"}
                className="input-field"
              />
              <select
                value={track.distribution_status}
                onChange={(e) => updateTrack(i, { distribution_status: e.target.value as DistributionStatus })}
                className="input-field"
              >
                <option value="not_started">not started</option>
                <option value="in_review">in review</option>
                <option value="distributed">distributed</option>
              </select>
            </div>
          ))}
          {tracks.length < 2 && (
            <button
              type="button"
              onClick={() => setTracks((t) => [...t, EMPTY_TRACK])}
              className="text-xs text-gold-soft hover:underline"
            >
              + add a second track
            </button>
          )}
        </fieldset>

        <fieldset className="space-y-4">
          <legend className="font-mono text-[10px] tracking-[0.15em] text-muted-foreground uppercase">
            Episode
          </legend>
          <input
            value={episode.title}
            onChange={(e) => setEpisode((ep) => ({ ...ep, title: e.target.value }))}
            placeholder="Episode title, e.g. The Long Storm"
            className="input-field"
          />
          <div className="grid grid-cols-2 gap-3">
            <StatusSelect
              label="Script status"
              value={episode.script_status}
              onChange={(v) => setEpisode((ep) => ({ ...ep, script_status: v }))}
            />
            <StatusSelect
              label="Voice-casting status"
              value={episode.voice_casting_status}
              onChange={(v) => setEpisode((ep) => ({ ...ep, voice_casting_status: v }))}
            />
          </div>

          <label className="flex items-start gap-2 text-sm text-foreground/90">
            <input
              type="checkbox"
              checked={episode.camera_pacing_varied}
              onChange={(e) => setEpisode((ep) => ({ ...ep, camera_pacing_varied: e.target.checked }))}
              className="mt-1"
            />
            Scenes use more than one camera angle (varied pacing)
          </label>
          <input
            value={episode.camera_pacing_note}
            onChange={(e) => setEpisode((ep) => ({ ...ep, camera_pacing_note: e.target.value }))}
            placeholder="Camera-pacing note (optional)"
            className="input-field"
          />

          <label className="flex items-start gap-2 text-sm text-foreground/90">
            <input
              type="checkbox"
              checked={episode.cast_diversity_complete}
              onChange={(e) => setEpisode((ep) => ({ ...ep, cast_diversity_complete: e.target.checked }))}
              className="mt-1"
            />
            Cast includes a designed White, Latino, and Asian friend character
          </label>
          <input
            value={episode.cast_diversity_note}
            onChange={(e) => setEpisode((ep) => ({ ...ep, cast_diversity_note: e.target.value }))}
            placeholder="Cast-diversity note (optional)"
            className="input-field"
          />
        </fieldset>

        {error && (
          <p role="alert" className="rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
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
              <Clapperboard className="size-4" aria-hidden />
              Start asking the Director about my show
            </>
          )}
        </button>
      </form>
    </div>
  );
}

function StatusSelect({
  label,
  value,
  onChange,
}: {
  label: string;
  value: ProductionStatus;
  onChange: (v: ProductionStatus) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block font-mono text-[10px] tracking-[0.15em] text-muted-foreground uppercase">
        {label}
      </span>
      <select value={value} onChange={(e) => onChange(e.target.value as ProductionStatus)} className="input-field">
        <option value="not_started">not started</option>
        <option value="in_progress">in progress</option>
        <option value="done">done</option>
      </select>
    </label>
  );
}
