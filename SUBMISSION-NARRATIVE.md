# BrightKin Studio Director — Devpost Submission Narrative

## Tagline

One production question becomes an auditable decision: Gemini agents coordinate over live ClickHouse memory, with the route and SQL evidence shown to the user.

## Inspiration

Film and animation teams rarely lack data. They lack a trustworthy way to turn fragmented production events, creative standards, and delivery checks into a decision everyone can inspect. A producer asking “Can this episode advance?” should not need to reconcile dashboards, spreadsheets, and policy documents—or trust an AI answer with no evidence.

BrightKin Studio Director began as a focused answer to that problem: a Director agent for production status and a Compliance specialist for documented standards. We then introduced **Studio Mesh**, a new BrightKin orchestration layer that adds Greenlight and Release specialists without replacing the original product. Studio Director remains the coherent user experience; Studio Mesh lets it coordinate the right expertise behind each decision.

## What it does

Studio Director answers natural-language questions about a clearly labeled synthetic animated-series production snapshot stored in ClickHouse Cloud. It can:

- retrieve the latest stage and status from an append-only production log;
- explain what is blocking an episode or track;
- check cast-diversity, original-music, and camera-pacing standards;
- issue an evidence-based `GO`, `HOLD`, `READY`, or `NO_DATA` decision;
- let a judge enter a small fictional show snapshot through “Bring Your Own Show” and run the same tenant-scoped workflow;
- expose the responsible agent, delegation route, and exact SQL grounding evidence in the interface.

Studio Mesh interweaves four Google ADK agents:

1. **Director** owns intent, direct status questions, routing, and the final response.
2. **Compliance** evaluates the studio’s documented creative and policy rules.
3. **Greenlight** determines whether the latest production state can advance.
4. **Release** retrieves evidence through the official ClickHouse MCP server, combines the applicable gates, and determines whether an item can ship.

This is not four independent chatbots. They operate on the same tenant-scoped production memory, have distinct decision boundaries, and return one inspectable answer.

## How we built it

The agent network uses Google’s official Agent Development Kit and Gemini. The Director is the root ADK agent; Compliance, Greenlight, and Release are registered sub-agents with purpose-specific tools and instructions.

ClickHouse Cloud is the system’s operational memory, not a decorative integration:

- `production_events` is an append-only MergeTree log. Current state is derived with ClickHouse-native `argMax(..., ts)` rather than maintained in a mutable status table.
- `casting_and_assets` stores structured evidence for creative and delivery standards.
- every read and write is scoped by `tenant_id`;
- parameterized queries prevent the model from controlling tenant scope;
- rate-limit events are stored in a TTL-backed MergeTree table, avoiding a second datastore;
- the Release specialist calls the official `ClickHouse/mcp-clickhouse` server’s `run_query` tool through a FastMCP client at runtime;
- the UI shows the SQL extracted from the actual agent tool-call trace.

The product is a Next.js 16 interface with Python serverless APIs. The live demo is deliberately fail-closed: if Gemini or ClickHouse is unavailable, it returns an availability error instead of inventing production state.

## Challenges we ran into

The most important correction came from auditing the official rules, not from adding UI polish. Direct `clickhouse-connect` usage demonstrated a real database integration but did not satisfy the ClickHouse track’s explicit requirement to use the official MCP server. We added a real MCP client/server tool boundary to the Release workflow while retaining deterministic driver-based writes and rate limiting.

We also had to separate an unknown item from a failed standard, keep tenant routing outside model-controlled tool arguments, and distinguish an old resolved blocker from the latest production state. Those cases now have dedicated tests.

## Accomplishments we are proud of

- A coherent product experience rather than an agent diagram or technical proof of concept.
- Four agents with distinct responsibilities and visible handoffs.
- Official ClickHouse MCP usage at runtime.
- ClickHouse-native append-only current-state modeling.
- Real tenant-scoped “Bring Your Own Show” data intake.
- Auditable SQL evidence presented with every applicable answer.
- A fail-closed API and regression coverage for isolation, query construction, rate limiting, compliance, Greenlight, and Release decisions.

## What we learned

Multi-agent systems become useful when agents own decision boundaries, not personas. The strongest architecture was not “more agents”; it was one orchestrator, narrow specialists, one shared evidence plane, and a trace the user can challenge.

We also learned that partner technology creates the most value when it shapes the product architecture. ClickHouse’s append-only MergeTree model, `argMax`, TTL tables, high-speed analytical queries, and MCP interface directly enabled the workflow rather than merely satisfying a badge requirement.

## What is next

- replace the browser-generated tenant ID with authenticated studio accounts;
- store studio-configurable standards as versioned data;
- add slate-wide and cross-project Greenlight reviews;
- write approved agent decisions back as immutable production events;
- deploy the agent runtime on Google Cloud Agent Engine and the official MCP service as an independently observable production service;
- measure time-to-decision, blocked-work age, false escalation rate, and release-gate turnaround for real production teams.

## Judge test path

1. Ask: `What stage is track_demo_horizon at?`
2. Ask: `Does episode_demo_1 pass the camera pacing standard?`
3. Ask: `Should episode_demo_1 be greenlit to advance?`
4. Ask: `Is episode_demo_1 ready for release?`
5. Open the SQL evidence under each answer and compare the route shown for Director, Compliance, Greenlight, and Release.
6. Switch to “Try your own show,” add a fictional episode and track, then repeat the questions to verify tenant-scoped reuse of the same workflow.

## Built with

Google ADK, Gemini, ClickHouse Cloud, official `ClickHouse/mcp-clickhouse`, FastMCP, `clickhouse-connect`, Next.js, React, TypeScript, Python, and Vercel.
