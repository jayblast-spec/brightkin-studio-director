"use client";

import { useEffect, useRef, useState } from "react";
import { ArrowUp, Database, ShieldCheck, Clapperboard, Sparkles, Film, Wand2, CircleGauge, Rocket } from "lucide-react";
import { askStudioDirector, EXAMPLE_QUESTIONS, type DirectorReply } from "@/lib/studio-director-client";
import { checkTenantStatus, getOrCreateTenantId } from "@/lib/tenant-client";
import { TenantIntakeForm } from "@/components/bk/TenantIntakeForm";
import { useTimecode } from "@/lib/use-timecode";
import { cn } from "@/lib/utils";

type Message = { id: string; role: "user"; text: string } | ({ id: string; role: "agent" } & DirectorReply);
type Mode = "brightkin" | "own-show";

let seq = 0;
const nextId = () => `m${++seq}`;

export function DemoChat() {
  const tc = useTimecode();
  const [mode, setMode] = useState<Mode>("brightkin");
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [hasOwnShowData, setHasOwnShowData] = useState<boolean | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const logRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    // Reads/writes localStorage (an external system), not derived from other
    // component state - the same "sync with an external system on mount"
    // exception already used in ProductionDashboard.tsx's initial fetch.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTenantId(getOrCreateTenantId());
  }, []);

  useEffect(() => {
    const el = logRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, pending]);

  async function selectOwnShowMode() {
    setMode("own-show");
    setMessages([]);
    if (!tenantId) return;
    const status = await checkTenantStatus(tenantId);
    setHasOwnShowData(status.ok ? status.data.hasData : false);
  }

  function selectBrightKinMode() {
    setMode("brightkin");
    setMessages([]);
  }

  async function submit(question: string) {
    const q = question.trim();
    if (!q || pending) return;
    setInput("");
    setMessages((m) => [...m, { id: nextId(), role: "user", text: q }]);
    setPending(true);
    try {
      const reply = await askStudioDirector(q, mode === "own-show" ? tenantId ?? undefined : undefined);
      setMessages((m) => [...m, { id: nextId(), role: "agent", ...reply }]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          id: nextId(),
          role: "agent",
          agent: "director",
          text: "The Director couldn't reach the production database. Try that question again.",
        },
      ]);
    } finally {
      setPending(false);
    }
  }

  const showIntakeForm = mode === "own-show" && hasOwnShowData === false && tenantId;

  return (
    <div className="glass-panel grain relative overflow-hidden rounded-3xl">
      <div className="flex flex-wrap items-center gap-3 border-b border-[var(--hairline)] px-5 py-3.5">
        <span className="inline-flex items-center gap-1.5" aria-hidden>
          <span className="relative flex size-2">
            <span className="animate-pulse-ring absolute inline-flex size-full rounded-full bg-destructive" />
            <span className="relative inline-flex size-2 rounded-full bg-destructive" />
          </span>
          <span className="font-mono text-[10px] font-bold tracking-[0.2em] text-destructive">LIVE</span>
        </span>
        <p className="font-mono text-[11px] tracking-wider text-muted-foreground uppercase">
          studio-director · session
        </p>
        <span className="tabular ml-auto font-mono text-xs tracking-[0.15em] text-gold" aria-hidden>
          {tc}
        </span>
      </div>

      <div
        role="tablist"
        aria-label="Data source"
        className="flex flex-wrap gap-2 border-b border-[var(--hairline)] px-5 py-3.5"
      >
        <ModeTab
          active={mode === "brightkin"}
          onClick={selectBrightKinMode}
          icon={Film}
          label="Real BrightKin"
        />
        <ModeTab
          active={mode === "own-show"}
          onClick={selectOwnShowMode}
          icon={Wand2}
          label="Try your own show"
        />
      </div>

      {mode === "own-show" && (
        <p className="px-5 pt-4 text-xs leading-relaxed text-muted-foreground">
          Answers in this mode are grounded only in the facts you submit below - a private,
          per-browser id, never the canonical synthetic snapshot.
        </p>
      )}

      {showIntakeForm ? (
        <div className="p-5">
          <TenantIntakeForm tenantId={tenantId} onSubmitted={() => setHasOwnShowData(true)} />
        </div>
      ) : (
        <ChatBody
          mode={mode}
          messages={messages}
          pending={pending}
          input={input}
          setInput={setInput}
          submit={submit}
          logRef={logRef}
        />
      )}
    </div>
  );
}

function ModeTab({
  active,
  onClick,
  icon: Icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: typeof Film;
  label: string;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3.5 py-2 text-[13px] font-medium transition-colors",
        active
          ? "border-gold/50 bg-gold/10 text-gold-soft"
          : "border-[var(--hairline)] bg-surface/60 text-muted-foreground hover:border-gold/30 hover:text-foreground"
      )}
    >
      <Icon className="size-3.5" aria-hidden />
      {label}
    </button>
  );
}

function ChatBody({
  mode,
  messages,
  pending,
  input,
  setInput,
  submit,
  logRef,
}: {
  mode: Mode;
  messages: Message[];
  pending: boolean;
  input: string;
  setInput: (v: string) => void;
  submit: (q: string) => void;
  logRef: React.RefObject<HTMLDivElement | null>;
}) {
  return (
    <>
      <div className="flex flex-wrap gap-2 px-5 pt-5">
        {mode === "brightkin" &&
          EXAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => submit(q)}
            disabled={pending}
            className="group rounded-full border border-[var(--hairline)] bg-surface/60 px-3.5 py-2 text-left text-[13px] text-muted-foreground transition-all duration-150 hover:-translate-y-0.5 hover:border-gold/45 hover:text-foreground disabled:opacity-50"
          >
            <span className="mr-1.5 font-mono text-gold/80">›</span>
            {q}
          </button>
        ))}
      </div>

      <div
        ref={logRef}
        role="log"
        aria-live="polite"
        aria-label="Studio Director conversation"
        className="mt-5 h-[360px] space-y-4 overflow-y-auto px-5 pb-2"
      >
        {messages.length === 0 && !pending && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
            <Sparkles className="size-6 text-gold/70" aria-hidden />
            <p className="max-w-xs text-sm text-muted-foreground">
              Pick an example question, or ask your own. The Director decides whether it can
              answer - or whether Compliance should.
            </p>
          </div>
        )}

        {messages.map((m) =>
          m.role === "user" ? (
            <div key={m.id} className="flex justify-end">
              <p className="max-w-[80%] rounded-2xl rounded-br-md bg-surface-raised px-4 py-2.5 text-sm text-foreground">
                {m.text}
              </p>
            </div>
          ) : (
            <AgentMessage key={m.id} message={m} />
          )
        )}

        {pending && (
          <div className="flex items-center gap-2.5">
            <AgentBadge agent="director" />
            <span className="flex gap-1" aria-label="Director is thinking">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="size-1.5 animate-bounce rounded-full bg-gold/80"
                  style={{ animationDelay: `${i * 120}ms` }}
                />
              ))}
            </span>
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(input);
        }}
        className="flex items-center gap-2 border-t border-[var(--hairline)] p-4"
      >
        <label htmlFor="director-input" className="sr-only">
          Ask the Studio Director a question
        </label>
        <input
          id="director-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about an episode, a track, or a standard…"
          autoComplete="off"
          className="min-w-0 flex-1 rounded-xl border border-[var(--hairline)] bg-background/60 px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground/70 focus:border-gold/50 focus:outline-none"
        />
        <button
          type="submit"
          disabled={pending || !input.trim()}
          className="inline-flex items-center gap-1.5 rounded-xl px-4 py-3 text-sm font-semibold text-primary-foreground transition-transform duration-150 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
          style={{ backgroundImage: "var(--gradient-gold)" }}
        >
          Ask
          <ArrowUp className="size-4" aria-hidden />
        </button>
      </form>
    </>
  );
}

function AgentBadge({ agent }: { agent: DirectorReply["agent"] }) {
  const meta = {
    director: { label: "Director", Icon: Clapperboard, classes: "border-gold/35 bg-gold/10 text-gold-soft" },
    compliance: { label: "Compliance", Icon: ShieldCheck, classes: "border-cyan/35 bg-cyan/10 text-cyan" },
    greenlight: { label: "Greenlight", Icon: CircleGauge, classes: "border-emerald-400/35 bg-emerald-400/10 text-emerald-300" },
    release: { label: "Release", Icon: Rocket, classes: "border-violet-400/35 bg-violet-400/10 text-violet-300" },
  }[agent];
  const Icon = meta.Icon;
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[10px] tracking-widest uppercase",
        meta.classes
      )}
    >
      <Icon className="size-3" aria-hidden />
      {meta.label}
    </span>
  );
}

function AgentMessage({ message }: { message: Extract<Message, { role: "agent" }> }) {
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <AgentBadge agent={message.agent} />
        {message.route && <span className="text-[11px] text-muted-foreground">{message.route}</span>}
      </div>
      <div className="rounded-2xl rounded-tl-md border border-[var(--hairline)] bg-surface/70 px-4 py-3">
        <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground/90">{message.text}</p>
        {message.query && (
          <div className="mt-3 rounded-lg border border-[var(--hairline)] bg-background/60 p-3">
            <p className="mb-1.5 inline-flex items-center gap-1.5 font-mono text-[10px] tracking-widest text-muted-foreground uppercase">
              <Database className="size-3" aria-hidden />
              ClickHouse query
            </p>
            <code className="block font-mono text-[11px] leading-relaxed break-words text-gold-soft/85">
              {message.query}
            </code>
          </div>
        )}
      </div>
    </div>
  );
}
