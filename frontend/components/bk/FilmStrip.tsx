"use client";

import type { LucideIcon } from "lucide-react";
import { useTimecode } from "@/lib/use-timecode";
import { Clapperboard, ShieldCheck } from "lucide-react";
import { TiltCard } from "@/components/bk/TiltCard";

export type FilmStep = {
  n: string;
  title: string;
  icon: LucideIcon;
  body: string;
  tag: string;
};

const RULER_TICKS = Array.from({ length: 48 });
const SPROCKETS = Array.from({ length: 12 });

/**
 * The Director → Compliance → ClickHouse handoff, rendered as a literal
 * 35mm film strip: sprocket-hole rails, a timeline ruler with a running
 * timecode playhead, and three numbered frames. This replaces a generic
 * three-card grid with a diagram a judge can read the agent routing from
 * at a glance - the middle frame renders the actual Director → Compliance
 * handoff as a small node-and-line diagram, not just an icon.
 */
export function FilmStrip({ steps }: { steps: FilmStep[] }) {
  const tc = useTimecode();

  return (
    <div className="relative overflow-hidden rounded-2xl border border-gold/20 bg-surface/40 shadow-[var(--shadow-depth)]">
      <Ruler tc={tc} />

      <div className="flex">
        <SprocketRail />

        <ol className="grid flex-1 grid-cols-1 divide-y divide-[var(--hairline)] md:grid-cols-3 md:divide-x md:divide-y-0">
          {steps.map((s, i) => (
            <li key={s.n} className={i === 1 ? "relative bg-gold/[0.04]" : "relative"} style={{ perspective: "1000px" }}>
              <TiltCard intensity={4} className="h-full">
                <div className="flex h-full flex-col p-7">
                  <span
                    className={`font-mono text-[10px] tracking-[0.2em] uppercase ${
                      i === 1 ? "font-bold text-gold" : "text-muted-foreground/60"
                    }`}
                  >
                    {s.n} · {i === 0 ? "input" : i === 1 ? "logic · active" : "output"}
                  </span>

                  <div className="my-6 flex h-16 items-center justify-center">
                    {i === 1 ? <HandoffDiagram /> : (
                      <span
                        className="tilt-layer flex size-12 items-center justify-center rounded-xl border border-[var(--hairline)] bg-background/60"
                        aria-hidden
                      >
                        <s.icon className="size-5 text-gold-soft" />
                      </span>
                    )}
                  </div>

                  <h3
                    className={`text-lg font-semibold uppercase tracking-wide ${i === 1 ? "text-gold" : "text-foreground"}`}
                  >
                    {s.title}
                  </h3>
                  <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{s.body}</p>
                  <p className="mt-6 inline-flex w-fit items-center gap-1.5 rounded-full border border-[var(--hairline)] px-2.5 py-1 font-mono text-[10px] tracking-[0.14em] text-muted-foreground uppercase">
                    {s.tag}
                  </p>
                </div>
              </TiltCard>
            </li>
          ))}
        </ol>

        <SprocketRail />
      </div>

      <Ruler tc={tc} flip />

      <p className="sr-only">Current session timecode {tc}</p>
    </div>
  );
}

function HandoffDiagram() {
  return (
    <div className="flex items-center gap-3" aria-hidden>
      <span className="tilt-layer flex size-10 items-center justify-center rounded-lg border border-gold/50 bg-gold/10">
        <Clapperboard className="size-4 text-gold" />
      </span>
      <span className="relative h-px w-10 bg-gold/60">
        <span className="animate-pulse-ring absolute top-1/2 right-0 size-1.5 -translate-y-1/2 rounded-full bg-gold" />
        <span className="absolute top-1/2 right-0 size-1.5 -translate-y-1/2 rounded-full bg-gold" />
      </span>
      <span className="tilt-layer flex size-10 items-center justify-center rounded-full border border-cyan/50 bg-cyan/10">
        <ShieldCheck className="size-4 text-cyan" />
      </span>
    </div>
  );
}

function Ruler({ tc, flip = false }: { tc: string; flip?: boolean }) {
  return (
    <div
      aria-hidden
      className={`relative flex h-9 items-center overflow-hidden border-cyan/15 bg-background/60 px-6 ${
        flip ? "border-t" : "border-b"
      }`}
    >
      <div className={`flex h-full flex-1 items-end gap-[7px] opacity-50 ${flip ? "rotate-180 items-start" : ""}`}>
        {RULER_TICKS.map((_, i) => (
          <span
            key={i}
            className="w-px shrink-0 bg-cyan/50"
            style={{ height: i % 6 === 0 ? "14px" : "6px" }}
          />
        ))}
      </div>
      {!flip && (
        <span className="absolute left-1/2 flex -translate-x-1/2 flex-col items-center">
          <span className="size-1.5 rounded-sm bg-gold shadow-[0_0_10px_oklch(0.82_0.13_76/60%)]" />
          <span className="tabular mt-0.5 rounded-sm border border-gold/40 bg-background px-1 font-mono text-[9px] text-gold-soft">
            {tc}
          </span>
        </span>
      )}
    </div>
  );
}

function SprocketRail() {
  return (
    <div aria-hidden className="hidden w-6 shrink-0 flex-col items-center justify-around bg-surface-raised py-3 sm:flex">
      {SPROCKETS.map((_, i) => (
        <span key={i} className="h-2 w-3 rounded-[2px] bg-background shadow-[inset_0_1px_2px_rgba(0,0,0,0.7)]" />
      ))}
    </div>
  );
}
