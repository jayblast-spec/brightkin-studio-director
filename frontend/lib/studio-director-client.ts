export type Agent = "director" | "compliance";

export type DirectorReply = {
  /** Which agent produced the final answer. */
  agent: Agent;
  /** Answer body, rendered as plain text. */
  text: string;
  /** Display rendering of the parameterized ClickHouse query, when available. */
  query?: string;
  /** Short routing note ("delegated to Compliance"). */
  route?: string;
};

export const EXAMPLE_QUESTIONS = [
  "What stage is track_demo_horizon at?",
  "Does episode_demo_1 meet the diversity standard?",
  "Does track_demo_horizon meet the music originality policy?",
  "Does episode_demo_1 pass the camera pacing standard?",
];

/** tenantId is optional - omit it (or pass the canonical BrightKin id) to
 * query the bundled synthetic snapshot
 * existed. Pass a tester's own tenant id to scope the Director/Compliance
 * agents' ClickHouse queries to that tester's submitted data instead. */
export async function askStudioDirector(question: string, tenantId?: string): Promise<DirectorReply> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, tenant_id: tenantId }),
  });
  const data = await res.json();
  if (!res.ok || data.error) {
    return { agent: "director", text: data.error ?? "Couldn't reach the production log." };
  }
  return {
    agent: data.agent === "compliance" ? "compliance" : "director",
    text: data.answer,
    query: data.query ?? undefined,
    route: data.route ?? undefined,
  };
}
