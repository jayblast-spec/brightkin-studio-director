# Eligibility notes — Google Cloud Agentic Cinema Hackathon

Written 2026-09-01 as an honest, verifiable record of how this project's AI usage maps to the
official contest rules, because development on this repo used Claude Code (Anthropic) as a
coding assistant and the rules mention "Anthropic AI tools" in a restricted list. This document
exists so a judge or organizer can check the claim themselves rather than take our word for it.

## Exact rule text (Official Rules, Section 7.B, "Limitation on Artificial Intelligence Usage")

> "Projects may only use Google Cloud artificial intelligence tools, as detailed at
> https://cloud.google.com/terms/services (with examples including Gemini models on Agent
> Platform, BigQuery ML, and relevant APIs), and the built-in AI-powered features of the specific
> Partner's product relevant to your chosen track. No other AI models, agent frameworks, or AI
> APIs are permitted, regardless of vendor — this includes but is not limited to AWS, Microsoft,
> OpenAI, and Anthropic AI tools. This restriction applies only to AI/agent tooling; it does not
> restrict your use of other non-AI third-party services (e.g., hosting, databases, standard web
> frameworks)."

Retrieved via the Devpost hackathon-rules API for `agentic-cinema` on 2026-09-01.

## Our reading: this restricts what the *Project* runs, not what tool wrote the code

The clause is under "SUBMISSION REQUIREMENTS → What to Create," listing constraints on the
*Project* — the built software being judged — not on the entrant's development process. It
restricts which "AI models, agent frameworks, or AI APIs" the *Project* is permitted to use.
"Anthropic AI tools" appears in a list alongside AWS and Microsoft, i.e. as an example of a
*competing AI vendor whose models/APIs the running product must not call* — not as a ban on
IDEs or coding assistants used to write the code.

Two pieces of supporting evidence:

1. **The Replit and IBM track requirements, in the same rules document, explicitly separate
   "development process" tooling from the Project's runtime stack** — e.g. "your project must be
   built using Replit Agent as part of the development process, and the finished project must be
   hosted and deployed directly on Replit," and "Use of ClickHouse Agent Skills during
   development is optional but encouraged." These clauses only make sense if development-time
   AI tooling is treated as a distinct, ordinarily-unregulated category from the Project's live
   AI/agent stack — otherwise naming a specific *development-process* tool as a track
   requirement would be redundant with the AI-usage limitation.
2. **Organizer language in the official hackathon announcements** (ClickHouse Build Session
   announcement, ~2026-08-18) describes the restriction itself as a "runtime requirement":
   "We'll run real analytical queries live and structure the integration to meet the hackathon's
   actual runtime requirement." This is the organizers' own framing of what Section 7.B checks —
   the live, running integration, not the development toolchain.

No forum thread or announcement was found that directly asks "does a coding assistant like
Claude Code / GitHub Copilot / Cursor count as a restricted AI tool," so this is our best-evidence
reading, not a confirmed organizer ruling. See "Open question for organizers" below.

## Current runtime dependency inventory (verified against source, 2026-09-01)

`frontend/requirements.txt` (backend, Vercel Python function):
```
google-adk>=2.7.1        # Google — the only agent-orchestration framework the Project runs
clickhouse-connect>=0.7.0  # ClickHouse Cloud client (Partner track requirement)
mcp-clickhouse>=0.3.0      # Official ClickHouse MCP server (Partner track requirement)
fastmcp>=2.0.0              # MCP protocol library, not an AI vendor SDK
python-dotenv>=1.0.0
dnspython>=2.6.0
```

`frontend/package.json` `dependencies` (frontend):
```
next, react, react-dom, tailwindcss, @tailwindcss/postcss, clsx, lucide-react,
tw-animate-css, tailwind-merge
```
— plain Next.js/React/Tailwind, no AI SDK of any vendor.

**There is no Anthropic (or AWS/Microsoft/OpenAI) AI model, agent framework, or AI API imported
or called anywhere in the running application.** The only LLM the deployed agents call is Gemini,
via Google's `google-adk`, at the API layer google-adk itself uses (Gemini Developer API,
`gemini-flash-lite-latest`). ClickHouse is the Partner track's required data layer, not an AI
tool. This can be verified directly by grepping `frontend/requirements.txt`,
`frontend/agents/*.py`, and `frontend/api/*.py` for any non-Google, non-ClickHouse AI import —
there is none.

## Development-tool disclosure

Claude Code (Anthropic) was used during development as a coding assistant — writing and editing
source files, running builds/tests, and deploying via the Vercel CLI. It was not integrated into
the shipped Project: it does not run at request time, is not imported by any runtime module, and
a user interacting with the live app never calls it. This is the same category of tool as an IDE,
linter, or GitHub Copilot — assistive to the person writing the code, not part of what the
Project executes.

We are not claiming this Project was "built exclusively with Gemini" in the sense of every line
being AI-generated by Gemini alone — it was built by a human developer using Claude Code as an
assistant, with the *shipped product's* AI functionality running exclusively on Gemini/Google
Cloud AI per the rule's actual restriction.

## Open question for organizers

If this reading is wrong and the "Anthropic AI tools" restriction is meant to reach
development-time coding assistants (not just the Project's runtime AI stack), we would want to
know before the 2026-09-09 deadline. Draft question, ready to post to the hackathon's official
forum/Discord if Joy wants to send it:

> "Section 7.B restricts 'Anthropic AI tools' among others. Does this restrict AI coding
> assistants (e.g. Claude Code, GitHub Copilot, Cursor) used during development, or only AI
> models/APIs the submitted Project calls at runtime? Our Project's runtime stack is 100%
> Google ADK + Gemini + ClickHouse (per the ClickHouse track requirement) — we used an
> Anthropic coding assistant only to help write the code, the same way one might use an IDE
> or Copilot. Want to confirm that's compliant before the deadline."

## What we are not doing

We are not rebuilding or rewriting this project's history to conceal that Claude Code was used
in development. That would misrepresent how the Project was actually built, which the rules'
"original creation" clause and general contest integrity requirements make clearly worse than
disclosing accurately. If organizer clarification narrows this reading, the minimum legitimate
remediation is to redo the *remaining* development work (if any is left before the deadline)
using only Gemini-based tooling going forward, and to disclose the mixed development history
in the Devpost submission — not to falsify a single-tool origin story.
