"use client";

import Link from "next/link";
import { ArrowUpRight, Clapperboard, Database, LayoutDashboard, MessageSquareText, ShieldCheck, Split } from "lucide-react";
import { AgentNetwork } from "@/components/bk/AgentNetwork";
import { DemoChat } from "@/components/bk/DemoChat";
import { FilmStrip } from "@/components/bk/FilmStrip";
import { Grain } from "@/components/bk/Grain";
import { Reveal } from "@/components/bk/Reveal";
import { TiltCard } from "@/components/bk/TiltCard";
import { Viewfinder } from "@/components/bk/Viewfinder";

const STEPS = [
  {
    n: "01",
    title: "Ask",
    icon: MessageSquareText,
    body: "Ask a plain-language question about an episode or a track. No SQL, no dashboard hunting, no knowing which table holds the answer.",
    tag: "natural language in",
  },
  {
    n: "02",
    title: "Director decides",
    icon: Split,
    body: "The Director agent answers production-status questions directly, and delegates standards questions to the Compliance sub-agent. Routing is part of the answer, not hidden behind it.",
    tag: "agent handoff",
  },
  {
    n: "03",
    title: "Grounded answer",
    icon: Database,
    body: "Every answer is routed through a ClickHouse query against a clearly labeled synthetic snapshot. The UI exposes the query used for grounding.",
    tag: "query-grounded",
  },
];

export default function Landing() {
  return (
    <div className="relative min-h-screen bg-background">
      <Grain />
      <Ambience />
      <Header />
      <main>
        <Hero />
        <HowItWorks />
        <TryIt />
      </main>
      <Footer />
    </div>
  );
}

function Ambience() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 overflow-hidden">
      <div
        className="parallax-near absolute -top-40 left-1/2 h-[540px] w-[900px] -translate-x-1/2 rounded-full opacity-60 blur-[120px]"
        style={{
          background: "radial-gradient(ellipse at center, oklch(0.82 0.13 76 / 16%), transparent 65%)",
        }}
      />
      <div
        className="parallax-far absolute top-[70vh] -right-40 h-[460px] w-[560px] rounded-full opacity-50 blur-[130px]"
        style={{
          background: "radial-gradient(ellipse at center, oklch(0.78 0.1 210 / 12%), transparent 65%)",
        }}
      />
      <div
        className="absolute inset-0 opacity-[0.35]"
        style={{
          backgroundImage:
            "linear-gradient(oklch(1 0 0 / 3%) 1px, transparent 1px), linear-gradient(90deg, oklch(1 0 0 / 3%) 1px, transparent 1px)",
          backgroundSize: "78px 78px",
          maskImage: "radial-gradient(ellipse 80% 55% at 50% 0%, #000 40%, transparent 100%)",
        }}
      />
    </div>
  );
}

function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--hairline)] bg-background/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
        <a href="#top" className="group inline-flex items-center gap-2.5">
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
        </a>
        <nav aria-label="Primary" className="flex items-center gap-1.5">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 rounded-lg border border-[var(--hairline)] bg-surface/50 px-3 py-2 text-sm text-foreground transition-colors hover:border-gold/40"
          >
            <LayoutDashboard className="size-3.5 text-gold" aria-hidden />
            Dashboard
          </Link>
          {[
            { label: "GitHub", href: "https://github.com/jayblast-spec/brightkin-studio-director" },
            { label: "Devpost", href: "https://devpost.com/software/brightkin-studio-director" },
          ].map((l) => (
            <a
              key={l.label}
              href={l.href}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 rounded-lg border border-transparent px-3 py-2 text-sm text-muted-foreground transition-colors hover:border-[var(--hairline)] hover:text-foreground"
            >
              {l.label}
              <ArrowUpRight className="size-3.5 opacity-60" aria-hidden />
            </a>
          ))}
        </nav>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section id="top" className="relative overflow-hidden">
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 py-20 sm:px-8 lg:grid-cols-[1.05fr_0.95fr] lg:py-28">
        <div>
          <Reveal>
            <div className="flex flex-wrap items-center gap-2.5">
              <p className="inline-flex items-center gap-2 rounded-full border border-[var(--hairline)] bg-surface/50 px-3 py-1.5 font-mono text-[11px] tracking-[0.14em] text-muted-foreground uppercase">
                <span className="size-1.5 rounded-full bg-gold" aria-hidden />
                Agentic Cinema Hackathon · ClickHouse Track
              </p>
              <p className="inline-flex items-center gap-1.5 rounded-full border border-cyan/30 bg-cyan/10 px-3 py-1.5 font-mono text-[11px] tracking-[0.14em] text-cyan uppercase">
                <Clapperboard className="size-3" aria-hidden />
                Prod_Mode: Active
              </p>
            </div>
          </Reveal>

          <Reveal delay={90}>
            <h1 className="mt-7 text-[clamp(3rem,9vw,5.75rem)] leading-[0.94] font-semibold">
              <span className="block">Studio</span>
              <span className="text-gradient-gold block">Director</span>
            </h1>
          </Reveal>

          <Reveal delay={180}>
            <p className="mt-7 max-w-xl text-[17px] leading-relaxed text-muted-foreground">
              A Director agent and a Compliance sub-agent - built on Google&apos;s Agent Development
              Kit and Gemini - that answer questions about a synthetic animated-series production
              snapshot stored in ClickHouse. Demo data verified 2026-08-01 UTC.
            </p>
          </Reveal>

          <Reveal delay={260}>
            <div className="mt-9 flex flex-wrap items-center gap-3">
              <a
                href="#try-it"
                className="inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-semibold text-primary-foreground transition-transform duration-150 hover:-translate-y-0.5 active:translate-y-0 active:scale-[0.98]"
                style={{ backgroundImage: "var(--gradient-gold)" }}
              >
                Try the Director
              </a>
              <a
                href="#how-it-works"
                className="inline-flex items-center gap-2 rounded-xl border border-[var(--hairline)] bg-surface/50 px-5 py-3 text-sm font-medium text-foreground transition-colors hover:border-gold/40"
              >
                How it works
              </a>
            </div>
          </Reveal>

          <Reveal delay={340}>
            <dl className="mt-12 grid max-w-md grid-cols-3 gap-6 border-t border-[var(--hairline)] pt-6">
              {[
                ["2", "agents"],
                ["1", "queried warehouse"],
                ["1", "synthetic snapshot"],
              ].map(([v, k]) => (
                <div key={k}>
                  <dt className="sr-only">{k}</dt>
                  <dd>
                    <span className="tabular font-display block text-2xl font-semibold text-foreground">{v}</span>
                    <span className="mt-1 block font-mono text-[10px] tracking-[0.15em] text-muted-foreground uppercase">
                      {k}
                    </span>
                  </dd>
                </div>
              ))}
            </dl>
          </Reveal>
        </div>

        <Reveal delay={160} className="relative">
          <TiltCard intensity={5} className="relative">
            <div className="glow-gold rounded-2xl">
              <Viewfinder caption="DIRECTOR ⇄ COMPLIANCE ⇄ CLICKHOUSE">
                <AgentNetwork className="block h-[340px] w-full sm:h-[400px]" />
                <div className="tilt-layer pointer-events-none absolute top-3 left-1/2 -translate-x-1/2 rounded-full border border-[var(--hairline)] bg-background/80 px-2.5 py-1 font-mono text-[10px] tracking-wider text-gold-soft uppercase">
                  ADK · Gemini
                </div>
              </Viewfinder>
            </div>
          </TiltCard>
        </Reveal>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section id="how-it-works" aria-labelledby="how-it-works-heading" className="relative py-24 sm:py-32">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <Reveal>
          <p className="font-mono text-[11px] tracking-[0.2em] text-gold uppercase">How it works</p>
          <h2 id="how-it-works-heading" className="mt-4 max-w-2xl text-[clamp(2rem,4.5vw,3rem)] leading-tight font-semibold">
            One question in. A routed, grounded answer out.
          </h2>
        </Reveal>

        <Reveal delay={100} className="mt-14">
          <FilmStrip steps={STEPS} />
        </Reveal>

        <Reveal delay={200}>
          <div className="mt-8 flex flex-wrap items-center gap-x-8 gap-y-3 rounded-2xl border border-[var(--hairline)] bg-surface/40 px-6 py-5">
            <span className="inline-flex items-center gap-2 text-sm text-muted-foreground">
              <Clapperboard className="size-4 text-gold" aria-hidden />
              Director - production status, stages, schedule
            </span>
            <span className="inline-flex items-center gap-2 text-sm text-muted-foreground">
              <ShieldCheck className="size-4 text-cyan" aria-hidden />
              Compliance - standards, policies, pass/fail
            </span>
          </div>
        </Reveal>
      </div>
    </section>
  );
}

function TryIt() {
  return (
    <section id="try-it" aria-labelledby="try-it-heading" className="relative py-8 pb-28 sm:pb-36">
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
        <Reveal>
          <p className="font-mono text-[11px] tracking-[0.2em] text-gold uppercase">Try it</p>
          <h2 id="try-it-heading" className="mt-4 max-w-2xl text-[clamp(2rem,4.5vw,3rem)] leading-tight font-semibold">
            Put a question to the Director.
          </h2>
          <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-muted-foreground">
            This runs the deployed agent and a fresh ClickHouse query against the bundled synthetic
            snapshot (verified 2026-08-01 UTC). Each answer shows which agent handled it and the
            query used for grounding.
          </p>
        </Reveal>

        <Reveal delay={120} className="mt-10">
          <DemoChat />
        </Reveal>
      </div>
    </section>
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
