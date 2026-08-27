"use client";

import type { ReactNode } from "react";
import { useTimecode } from "@/lib/use-timecode";

/**
 * A camera-viewfinder / broadcast-monitor bezel: top bar with a tally light
 * and a real running timecode, corner brackets, bottom bar with lens/network
 * metadata. Wraps arbitrary diagram content (e.g. the AgentNetwork canvas).
 */
export function Viewfinder({ children, caption }: { children: ReactNode; caption: string }) {
  const tc = useTimecode();

  return (
    <div
      className="depth-tilt relative overflow-hidden rounded-2xl border border-[var(--hairline)] bg-background/70 shadow-[var(--shadow-depth)]"
      style={{ perspective: "1400px" }}
    >
      <div className="flex items-center justify-between border-b border-[var(--hairline)] bg-surface/70 px-4 py-2.5">
        <span className="tally-warm inline-flex items-center gap-2">
          <span className="relative flex size-2" aria-hidden>
            <span className="animate-pulse-ring absolute inline-flex size-full rounded-full bg-destructive" />
            <span className="relative inline-flex size-2 rounded-full bg-destructive" />
          </span>
          <span className="font-mono text-[10px] font-bold tracking-[0.25em] text-destructive">LIVE</span>
        </span>
        <span
          className="readout-in tabular font-mono text-sm font-semibold tracking-[0.15em] text-gold"
          style={{ animationDelay: "0.55s" }}
          aria-hidden
        >
          {tc}
        </span>
        <span className="readout-in inline-flex items-center gap-1.5 opacity-60" style={{ animationDelay: "0.65s" }}>
          <span className="size-1.5 rounded-full bg-foreground" aria-hidden />
          <span className="font-mono text-[10px] tracking-[0.2em] text-foreground">REC</span>
        </span>
      </div>

      <div className="relative" style={{ transform: "translateZ(0)" }}>
        {/* Scanning sweep - a single pass on power-on, reads as the monitor
            settling into signal rather than a looping decorative gimmick. */}
        <span
          aria-hidden
          className="scan-sweep pointer-events-none absolute inset-x-0 top-0 z-10 h-1/3 opacity-[0.06]"
          style={{
            background: "linear-gradient(180deg, transparent, oklch(0.82 0.13 76 / 60%), transparent)",
            animationIterationCount: 1,
            animationDuration: "0.9s",
          }}
        />
        {children}
      </div>

      <div className="flex items-center justify-between border-t border-[var(--hairline)] bg-surface/70 px-4 py-2.5">
        <span className="readout-in font-mono text-[10px] tracking-[0.2em] text-muted-foreground" style={{ animationDelay: "0.7s" }}>
          LENS F/2.8
        </span>
        <p className="readout-in font-mono text-[10px] tracking-[0.15em] text-muted-foreground" style={{ animationDelay: "0.75s" }}>
          {caption}
        </p>
        <span className="readout-in flex flex-col items-end leading-tight" style={{ animationDelay: "0.8s" }}>
          <span className="font-mono text-[10px] font-bold tracking-[0.2em] text-gold">ISO 800</span>
          <span className="font-mono text-[9px] tracking-[0.15em] text-cyan">NET STATUS: OPTIMAL</span>
        </span>
      </div>

      {/* Corner brackets - decorative viewfinder chrome, snap into frame in
          sequence (top pair, then bottom pair) like a lens racking into focus. */}
      <div aria-hidden className="pointer-events-none absolute inset-0">
        {([
          ["top-3 left-3 border-t border-l", "0s"],
          ["top-3 right-3 border-t border-r", "0.08s"],
          ["bottom-14 left-3 border-b border-l", "0.16s"],
          ["bottom-14 right-3 border-b border-r", "0.24s"],
        ] as const).map(([pos, delay]) => (
          <span
            key={pos}
            className={`bracket-in absolute size-5 ${pos} border-gold/50`}
            style={{ animationDelay: delay }}
          />
        ))}
      </div>
    </div>
  );
}
