from google.adk.agents import Agent

from agents.tool_wrappers import tool_assess_release, tool_mcp_release_evidence


release_agent = Agent(
    name="release_agent",
    model="gemini-flash-lite-latest",
    instruction=(
        "You are BrightKin Studio Mesh's Release agent. Determine whether an episode or track can "
        "ship by first calling tool_mcp_release_evidence, then tool_assess_release. Report the exact "
        "readiness decision and every evidence "
        "gap. Never turn a missing record into a failure and never invent production state."
    ),
    tools=[tool_mcp_release_evidence, tool_assess_release],
)
