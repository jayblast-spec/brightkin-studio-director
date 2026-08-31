"use client";

import { useEffect, useRef } from "react";

type Node = {
  x: number;
  y: number;
  z: number;
  r: number;
  kind: "agent" | "data";
};

/**
 * Abstract 3D-ish network: four orbiting "agent" cores exchanging packets with a
 * lattice of database nodes. Pure canvas, no dependencies.
 */
export function AgentNetwork({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let w = 0;
    let h = 0;
    let dpr = 1;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = rect.width;
      h = rect.height;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const nodes: Node[] = [];
    const RING = 26;
    for (let i = 0; i < RING; i++) {
      const a = (i / RING) * Math.PI * 2;
      const rad = 0.34 + (i % 3) * 0.055;
      nodes.push({
        x: Math.cos(a) * rad,
        y: Math.sin(a) * rad * 0.46,
        z: Math.sin(a * 2 + i) * 0.3,
        r: 1.4 + (i % 4) * 0.5,
        kind: "data",
      });
    }
    nodes.push({ x: -0.16, y: -0.2, z: 0.4, r: 5, kind: "agent" });
    nodes.push({ x: 0.2, y: 0.16, z: -0.3, r: 4, kind: "agent" });
    nodes.push({ x: -0.2, y: 0.17, z: -0.25, r: 4, kind: "agent" });
    nodes.push({ x: 0.17, y: -0.17, z: 0.32, r: 4, kind: "agent" });

    type Packet = { from: number; to: number; t: number; speed: number };
    const packets: Packet[] = Array.from({ length: 14 }, () => ({
      from: Math.floor(Math.random() * RING),
      to: RING + Math.floor(Math.random() * 4),
      t: Math.random(),
      speed: 0.0022 + Math.random() * 0.0035,
    }));

    let t = 0;
    let frame = 0;

    const project = (n: Node, rot: number) => {
      const cos = Math.cos(rot);
      const sin = Math.sin(rot);
      const x = n.x * cos - n.z * sin;
      const z = n.x * sin + n.z * cos;
      const persp = 1 / (1.5 - z * 0.5);
      const s = Math.min(w, h * 1.7);
      return {
        sx: w / 2 + x * s * persp,
        sy: h / 2 + n.y * s * persp,
        depth: persp,
      };
    };

    const draw = () => {
      t += reduced ? 0 : 1;
      const rot = t * 0.0016;
      ctx.clearRect(0, 0, w, h);

      const pts = nodes.map((n) => project(n, rot));

      ctx.lineWidth = 1;
      for (let i = 0; i < RING; i++) {
        const a = pts[i];
        const b = pts[(i + 1) % RING];
        ctx.strokeStyle = `rgba(150,180,210,${0.05 + 0.05 * a.depth})`;
        ctx.beginPath();
        ctx.moveTo(a.sx, a.sy);
        ctx.lineTo(b.sx, b.sy);
        ctx.stroke();
      }

      for (let ai = RING; ai < nodes.length; ai++) {
        const agent = pts[ai];
        for (let i = 0; i < RING; i += 2) {
          const p = pts[i];
          ctx.strokeStyle = `rgba(255,184,77,${0.035 + 0.045 * p.depth})`;
          ctx.beginPath();
          ctx.moveTo(agent.sx, agent.sy);
          ctx.lineTo(p.sx, p.sy);
          ctx.stroke();
        }
      }

      const a0 = pts[RING];
      const a1 = pts[RING + 1];
      ctx.strokeStyle = "rgba(255,184,77,0.4)";
      ctx.lineWidth = 1.4;
      ctx.setLineDash([5, 7]);
      ctx.lineDashOffset = -t * 0.35;
      ctx.beginPath();
      ctx.moveTo(a0.sx, a0.sy);
      ctx.lineTo(a1.sx, a1.sy);
      ctx.stroke();
      ctx.setLineDash([]);

      for (let i = 0; i < RING; i++) {
        const p = pts[i];
        const n = nodes[i];
        ctx.fillStyle = `rgba(180,205,230,${0.22 + 0.4 * (p.depth - 0.6)})`;
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, n.r * p.depth, 0, Math.PI * 2);
        ctx.fill();
      }

      for (const pk of packets) {
        if (!reduced) pk.t += pk.speed;
        if (pk.t > 1) {
          pk.t = 0;
          pk.from = Math.floor(Math.random() * RING);
          pk.to = RING + Math.floor(Math.random() * 4);
        }
        const a = pts[pk.from];
        const b = pts[pk.to];
        const e = pk.t < 0.5 ? 2 * pk.t * pk.t : 1 - Math.pow(-2 * pk.t + 2, 2) / 2;
        const x = a.sx + (b.sx - a.sx) * e;
        const y = a.sy + (b.sy - a.sy) * e;
        const g = ctx.createRadialGradient(x, y, 0, x, y, 9);
        g.addColorStop(0, "rgba(255,205,130,0.9)");
        g.addColorStop(1, "rgba(255,184,77,0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(x, y, 9, 0, Math.PI * 2);
        ctx.fill();
      }

      for (let ai = RING; ai < nodes.length; ai++) {
        const p = pts[ai];
        const n = nodes[ai];
        const rr = n.r * p.depth * 2.2;
        const g = ctx.createRadialGradient(p.sx, p.sy, 0, p.sx, p.sy, rr * 5);
        g.addColorStop(0, "rgba(255,214,150,0.95)");
        g.addColorStop(0.25, "rgba(255,184,77,0.35)");
        g.addColorStop(1, "rgba(255,184,77,0)");
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, rr * 5, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = "rgba(255,236,205,0.95)";
        ctx.beginPath();
        ctx.arc(p.sx, p.sy, rr, 0, Math.PI * 2);
        ctx.fill();
      }

      frame = requestAnimationFrame(draw);
    };
    frame = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(frame);
      ro.disconnect();
    };
  }, []);

  return <canvas ref={canvasRef} aria-hidden className={className} />;
}
