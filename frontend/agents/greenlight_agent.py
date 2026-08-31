from google.adk.agents import Agent

from agents.tool_wrappers import tool_assess_greenlight


greenlight_agent = Agent(
    name="greenlight_agent",
    model="gemini-flash-lite-latest",
    instruction=(
        "You are BrightKin Studio Mesh's Greenlight agent. Assess whether a production item is "
        "ready to advance by calling tool_assess_greenlight. Report the current stage, blocking "
        "events, and a clear GO, HOLD, or NO_DATA decision. Never infer facts outside the tool result."
    ),
    tools=[tool_assess_greenlight],
)
