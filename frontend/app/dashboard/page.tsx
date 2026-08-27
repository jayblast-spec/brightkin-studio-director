"use client";

import Link from "next/link";
import { ArrowLeft, ArrowUpRight, Clapperboard, LayoutDashboard } from "lucide-react";
import { Grain } from "@/components/bk/Grain";
import { ProductionDashboard } from "@/components/bk/ProductionDashboard";
import { Reveal } from "@/components/bk/Reveal";

export default function DashboardPage() {
  return (
    <div className="relative min-h-screen bg-background">
      <Grain />
      <Header />
      <main className="mx-auto max-w-6xl px-5 py-14 sm:px-8 sm:py-20">
        <Reveal>
          <p className="inline-flex items-center gap-2 rounded-full border border-cyan/30 bg-cyan/10 px-3 py-1.5 font-mono text-[11px] tracking-[0.14em] text-cyan uppercase">
            <LayoutDashboard className="size-3" aria-hidden />
            Production Dashboard
          </p>
          <h1 className="mt-5 max-w-2xl text-[clamp(2.1rem,5vw,3.25rem)] leading-[1.02] font-semibold">
            Manage the real pipeline, not just query it.
          </h1>
          <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-muted-foreground">
            Log a new production event and it lands as a real row in ClickHouse&apos;s{" "}
            <code className="font-mono text-gold-soft">production_events</code> table - the same
            table the Director and Compliance agents already read from on the chat page. Nothing
            here is seeded or fixed; every row below is a live query result.
          </p>
        </Reveal>

        <Reveal delay={100} className="mt-10">
          <ProductionDashboard />
        </Reveal>
      </main>
      <Footer />
    </div>
  );
}

function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--hairline)] bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
        <Link href="/" className="group inline-flex items-center gap-2.5">
          <span
            className="flex size-7 items-center justify-center rounded-md"
            style={{ backgroundImage: "var(--gradient-gold)" }}
            aria-hidden
          >
            <Clapperboard className="size-4 text-primary-foreground" />
          </span>
          <span className="font-display text-[15px] font-semibold tracking-tight">
            BrightKin <span className="text-muted-foreground">Studio</span>
          </span>
        </Link>
        <nav aria-label="Primary" className="flex items-center gap-1.5">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 rounded-lg border border-transparent px-3 py-2 text-sm text-muted-foreground transition-colors hover:border-[var(--hairline)] hover:text-foreground"
          >
            <ArrowLeft className="size-3.5" aria-hidden />
            Chat
          </Link>
          <a
            href="https://github.com/jayblast-spec/brightkin-studio-director"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 rounded-lg border border-transparent px-3 py-2 text-sm text-muted-foreground transition-colors hover:border-[var(--hairline)] hover:text-foreground"
          >
            GitHub
            <ArrowUpRight className="size-3.5 opacity-60" aria-hidden />
          </a>
        </nav>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="relative border-t border-[var(--hairline)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-10 sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <p className="text-sm text-muted-foreground">Built for the Agentic Cinema hackathon.</p>
        <p className="font-mono text-[11px] tracking-[0.12em] text-muted-foreground/80">
          Google ADK · Gemini · ClickHouse Cloud · Next.js · Vercel
        </p>
      </div>
    </footer>
  );
}
