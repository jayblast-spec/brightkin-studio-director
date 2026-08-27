"use client";

import { useEffect, useRef } from "react";

/**
 * A real animated film-grain overlay for the page, rendered on canvas instead
 * of a static SVG turbulence texture. Each redraw is fresh per-pixel noise -
 * it flickers the way actual film grain does - sampled at low resolution and
 * upscaled by the browser so it stays soft rather than blocky, and redrawn
 * at a throttled ~11fps (not every animation frame) to keep it cheap.
 * Freezes to a single static frame under prefers-reduced-motion.
 */
export function Grain() {
  const ref = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const SCALE = 0.22;
    let w = 1;
    let h = 1;

    const resize = () => {
      w = Math.max(1, Math.floor(window.innerWidth * SCALE));
      h = Math.max(1, Math.floor(window.innerHeight * SCALE));
      canvas.width = w;
      canvas.height = h;
    };
    resize();
    window.addEventListener("resize", resize);

    const paint = () => {
      const frame = ctx.createImageData(w, h);
      const buf = frame.data;
      for (let i = 0; i < buf.length; i += 4) {
        const v = (Math.random() * 255) | 0;
        buf[i] = v;
        buf[i + 1] = v;
        buf[i + 2] = v;
        buf[i + 3] = 255;
      }
      ctx.putImageData(frame, 0, 0);
    };
    paint();

    if (reduced) {
      return () => window.removeEventListener("resize", resize);
    }

    const id = window.setInterval(paint, 90);
    return () => {
      window.clearInterval(id);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return (
    <canvas
      ref={ref}
      aria-hidden
      className="pointer-events-none fixed inset-0 z-40 h-screen w-screen opacity-[0.035] mix-blend-overlay"
    />
  );
}
