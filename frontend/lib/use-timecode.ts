"use client";

import { useEffect, useState } from "react";

/**
 * A real, running broadcast-style timecode (HH:MM:SS:FF) counted from mount.
 * Not decorative fake data - it genuinely advances with wall-clock time via
 * requestAnimationFrame, at a nominal 24fps frame column. Freezes under
 * prefers-reduced-motion so it reads as a static "session" readout instead
 * of a distracting ticker.
 */
export function useTimecode(fps = 24) {
  const [label, setLabel] = useState("00:00:00:00");

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const start = performance.now();
    let frame = 0;

    const pad = (n: number) => String(n).padStart(2, "0");
    const render = (elapsedMs: number) => {
      const totalFrames = Math.floor((elapsedMs / 1000) * fps);
      const h = Math.floor(totalFrames / (fps * 3600));
      const m = Math.floor((totalFrames / (fps * 60)) % 60);
      const s = Math.floor((totalFrames / fps) % 60);
      const f = totalFrames % fps;
      setLabel(`${pad(h)}:${pad(m)}:${pad(s)}:${pad(f)}`);
    };

    if (reduced) {
      render(0);
      return;
    }

    const tick = (now: number) => {
      render(now - start);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [fps]);

  return label;
}
