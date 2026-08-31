"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Clapperboard, X } from "lucide-react";
import { useTimecode } from "@/lib/use-timecode";
import { cn } from "@/lib/utils";

const SEEN_KEY = "bk_tour_seen";
const REPLAY_EVENT = "bk:tour:replay";

type Step = {
  target: string;
  title: string;
  body: string;
  placement?: "top" | "bottom";
};

const STEPS: Step[] = [
  {
    target: "hero",
    title: "Four agents. One live pipeline.",
    body: "Director, Compliance, Greenlight, and Release all answer from the same live ClickHouse warehouse - never a guess, never cached.",
    placement: "bottom",
  },
  {
    target: "agents",
    title: "Who answers what",
    body: "Director handles production status, Compliance checks it against BrightKin's standards, Greenlight decides GO or HOLD, and Release runs the combined evidence gate before anything ships.",
    placement: "top",
  },
  {
    target: "mode-toggle",
    title: "Real data, or your own",
    body: "Test it on BrightKin's real production fixture data, or switch to “Try your own show” and ground it in a couple of facts you submit yourself.",
    placement: "bottom",
  },
  {
    target: "ask",
    title: "Ask in plain language",
    body: "No SQL, no dashboard hunting. Pick an example question or type your own - the reply shows which agent handled it and the exact query it ran.",
    placement: "top",
  },
  {
    target: "dashboard-link",
    title: "Log a real event",
    body: "The dashboard writes a real row into production_events - the same table the agents read from. Nothing here is seeded on demand.",
    placement: "bottom",
  },
];

type Phase = "idle" | "slate" | "tour";

export function OnboardingTour() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [stepIndex, setStepIndex] = useState(0);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    // Reads matchMedia (an external system) on mount - same exception as
    // DemoChat.tsx's tenant-id sync.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setReducedMotion(window.matchMedia("(prefers-reduced-motion: reduce)").matches);

    let seen = false;
    try {
      seen = window.localStorage.getItem(SEEN_KEY) === "1";
    } catch {
      seen = false;
    }
    if (!seen) {
      setPhase("slate");
    }

    const onReplay = () => {
      setStepIndex(0);
      setPhase("slate");
    };
    window.addEventListener(REPLAY_EVENT, onReplay);
    return () => window.removeEventListener(REPLAY_EVENT, onReplay);
  }, []);

  const finish = useCallback(() => {
    setPhase("idle");
    try {
      window.localStorage.setItem(SEEN_KEY, "1");
    } catch {
      // localStorage unavailable (private mode, etc) - tour just won't remember
    }
  }, []);

  const startTour = useCallback(() => {
    setStepIndex(0);
    setPhase("tour");
  }, []);

  useEffect(() => {
    if (phase !== "tour") return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") finish();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [phase, finish]);

  if (phase === "idle") return null;

  if (phase === "slate") {
    return <TourSlate reducedMotion={reducedMotion} onDone={startTour} onSkip={finish} />;
  }

  return (
    <Spotlight
      step={STEPS[stepIndex]}
      index={stepIndex}
      total={STEPS.length}
      onNext={() => (stepIndex + 1 < STEPS.length ? setStepIndex((i) => i + 1) : finish())}
      onBack={() => setStepIndex((i) => Math.max(0, i - 1))}
      onSkip={finish}
    />
  );
}

export function TourReplayButton({ className }: { className?: string }) {
  return (
    <button
      type="button"
      onClick={() => window.dispatchEvent(new Event(REPLAY_EVENT))}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg border border-[var(--hairline)] bg-surface/50 px-3 py-2 text-sm text-muted-foreground transition-colors hover:border-gold/40 hover:text-foreground",
        className
      )}
    >
      <Clapperboard className="size-3.5 text-gold" aria-hidden />
      Replay tour
    </button>
  );
}

function TourSlate({
  reducedMotion,
  onDone,
  onSkip,
}: {
  reducedMotion: boolean;
  onDone: () => void;
  onSkip: () => void;
}) {
  const tc = useTimecode();
  const [struck, setStruck] = useState(false);

  useEffect(() => {
    if (reducedMotion) {
      const t = setTimeout(onDone, 400);
      return () => clearTimeout(t);
    }
    const strike = setTimeout(() => setStruck(true), 550);
    const done = setTimeout(onDone, 2200);
    return () => {
      clearTimeout(strike);
      clearTimeout(done);
    };
  }, [reducedMotion, onDone]);

  return (
    <div
      role="dialog"
      aria-label="Studio Director introduction"
      className="fixed inset-0 z-[100] flex items-center justify-center bg-background"
    >
      <button
        type="button"
        onClick={onSkip}
        className="absolute top-5 right-5 inline-flex items-center gap-1.5 rounded-lg border border-[var(--hairline)] bg-surface/60 px-3 py-2 font-mono text-[11px] tracking-widest text-muted-foreground uppercase transition-colors hover:border-gold/40 hover:text-foreground"
      >
        <X className="size-3.5" aria-hidden />
        Skip
      </button>

      <div className="flex flex-col items-center gap-6 px-6 text-center">
        <div
          className={cn(
            "relative w-[280px] origin-bottom transition-transform duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] sm:w-[360px]",
            struck ? "rotate-0" : "-rotate-[22deg]"
          )}
        >
          <div className="glass-panel grain overflow-hidden rounded-2xl">
            <div
              className="flex items-center justify-between px-4 py-2.5"
              style={{ backgroundImage: "var(--gradient-gold)" }}
            >
              {[0, 1, 2, 3, 4].map((i) => (
                <span key={i} className="h-4 w-6 skew-x-[-20deg] bg-background/85" />
              ))}
            </div>
            <div className="space-y-2.5 px-5 py-6 text-left font-mono text-[11px] tracking-[0.15em] text-muted-foreground uppercase">
              <Row label="Prod" value="Studio Director" />
              <Row label="Scene" value="Onboarding" />
              <Row label="Take" value="01" />
              <div className="!mt-4 flex items-center justify-between border-t border-[var(--hairline)] pt-3">
                <span className="inline-flex items-center gap-1.5 text-gold">
                  <Clapperboard className="size-3.5" aria-hidden />
                  Director ⇄ Compliance
                </span>
                <span className="tabular text-gold-soft">{tc}</span>
              </div>
            </div>
          </div>
        </div>

        <p
          className={cn(
            "font-display text-2xl font-semibold tracking-tight text-foreground transition-opacity duration-500 sm:text-3xl",
            struck ? "opacity-100" : "opacity-0"
          )}
        >
          Action.
        </p>
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-muted-foreground/70">{label}</span>
      <span className="text-foreground">{value}</span>
    </div>
  );
}

function Spotlight({
  step,
  index,
  total,
  onNext,
  onBack,
  onSkip,
}: {
  step: Step;
  index: number;
  total: number;
  onNext: () => void;
  onBack: () => void;
  onSkip: () => void;
}) {
  const [rect, setRect] = useState<DOMRect | null>(null);
  const cardRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = document.querySelector<HTMLElement>(`[data-tour="${step.target}"]`);
    if (!el) {
      // Reads the DOM (an external system) for the current step's target -
      // same exception as above.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setRect(null);
      return;
    }
    el.scrollIntoView({ block: "center", behavior: "smooth" });

    const update = () => setRect(el.getBoundingClientRect());
    const t = setTimeout(update, 260);
    window.addEventListener("resize", update);
    window.addEventListener("scroll", update, true);
    return () => {
      clearTimeout(t);
      window.removeEventListener("resize", update);
      window.removeEventListener("scroll", update, true);
    };
  }, [step.target]);

  const pad = 10;
  const hole = rect
    ? {
        top: rect.top - pad,
        left: rect.left - pad,
        width: rect.width + pad * 2,
        height: rect.height + pad * 2,
      }
    : null;

  const placement = step.placement ?? "bottom";
  const cardTop = hole
    ? placement === "bottom"
      ? Math.min(hole.top + hole.height + 16, window.innerHeight - 220)
      : Math.max(hole.top - 16, 16)
    : window.innerHeight / 2 - 90;

  return (
    <div className="fixed inset-0 z-[100]" role="dialog" aria-label={step.title}>
      {hole ? (
        <div
          className="absolute rounded-2xl transition-all duration-300"
          style={{
            top: hole.top,
            left: hole.left,
            width: hole.width,
            height: hole.height,
            boxShadow: "0 0 0 9999px oklch(0.1 0.01 260 / 82%)",
            border: "1px solid oklch(0.82 0.13 76 / 55%)",
          }}
        />
      ) : (
        <div className="absolute inset-0" style={{ background: "oklch(0.1 0.01 260 / 82%)" }} />
      )}

      <button
        type="button"
        onClick={onSkip}
        className="absolute top-5 right-5 inline-flex items-center gap-1.5 rounded-lg border border-[var(--hairline)] bg-surface/80 px-3 py-2 font-mono text-[11px] tracking-widest text-muted-foreground uppercase backdrop-blur-md transition-colors hover:border-gold/40 hover:text-foreground"
      >
        <X className="size-3.5" aria-hidden />
        Skip
      </button>

      <div
        ref={cardRef}
        className="glass-panel absolute w-[calc(100vw-2.5rem)] max-w-sm rounded-2xl p-5 transition-[top,left] duration-300"
        style={{
          top: cardTop,
          left: hole ? Math.min(Math.max(hole.left, 20), window.innerWidth - 380) : window.innerWidth / 2 - 180,
        }}
      >
        <p className="font-mono text-[10px] tracking-[0.2em] text-gold uppercase">
          Step {index + 1} / {total}
        </p>
        <h3 className="mt-2 font-display text-lg font-semibold text-foreground">{step.title}</h3>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{step.body}</p>

        <div className="mt-5 flex items-center justify-between">
          <div className="flex gap-1.5" aria-hidden>
            {Array.from({ length: total }).map((_, i) => (
              <span
                key={i}
                className={cn("size-1.5 rounded-full transition-colors", i === index ? "bg-gold" : "bg-[var(--hairline)]")}
              />
            ))}
          </div>
          <div className="flex items-center gap-2">
            {index > 0 && (
              <button
                type="button"
                onClick={onBack}
                className="rounded-lg border border-[var(--hairline)] px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                Back
              </button>
            )}
            <button
              type="button"
              onClick={onNext}
              className="inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-xs font-semibold text-primary-foreground transition-transform active:scale-[0.98]"
              style={{ backgroundImage: "var(--gradient-gold)" }}
            >
              {index + 1 === total ? "Done" : "Next"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
