import { ImageResponse } from "next/og";

export const runtime = "nodejs";
export const alt = "BrightKin Studio Director";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          background: "#0a0a0c",
          color: "#e8e8ec",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", color: "#ffb84d", fontSize: 28, fontWeight: 700, marginBottom: 24 }}>
          BRIGHTKIN STUDIO
        </div>
        <div style={{ display: "flex", fontSize: 64, fontWeight: 700, lineHeight: 1.1, marginBottom: 28 }}>
          Studio Mesh
        </div>
        <div style={{ display: "flex", fontSize: 28, color: "#8a8a92", maxWidth: 900, lineHeight: 1.4 }}>
          Director, Compliance, Greenlight &amp; Release agents, built on Google&apos;s ADK and Gemini, grounded in a live ClickHouse production log.
        </div>
        <div style={{ display: "flex", marginTop: 48, fontSize: 22, color: "#ffb84d" }}>
          Agentic Cinema Hackathon &middot; ClickHouse Track
        </div>
      </div>
    ),
    { ...size }
  );
}
