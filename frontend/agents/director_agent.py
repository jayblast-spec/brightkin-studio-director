from google.adk.agents import Agent
from agents.tool_wrappers import tool_query_status
from agents.compliance_agent import compliance_agent

director_agent = Agent(
    name="director_agent",
    model="gemini-flash-lite-latest",
    instruction=(
        "You are the Director agent for BrightKin Studio, an animated series production. "
        "Answer direct status questions ('what stage is X at', 'what's blocking X') yourself using "
        "tool_query_status. For any question about whether an episode or track meets BrightKin's "
        "diversity, music-originality, or camera-pacing standards, delegate to compliance_agent and "
        "relay its exact finding. Always ground answers in tool results, never assume."
    ),
    tools=[tool_query_status],
    sub_agents=[compliance_agent],
)
