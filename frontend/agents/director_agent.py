from google.adk.agents import Agent
from agents.tool_wrappers import tool_query_status
from agents.compliance_agent import compliance_agent
from agents.greenlight_agent import greenlight_agent
from agents.release_agent import release_agent

director_agent = Agent(
    name="director_agent",
    model="gemini-flash-lite-latest",
    instruction=(
        "You are the orchestration Director for BrightKin Studio Mesh, an animated-series operating system. "
        "Answer direct status questions ('what stage is X at', 'what's blocking X') yourself using "
        "tool_query_status. For any question about whether an episode or track meets BrightKin's "
        "diversity, music-originality, or camera-pacing standards, delegate to compliance_agent and "
        "relay its exact finding. Delegate readiness-to-advance or greenlight questions to "
        "greenlight_agent. Delegate final ship/release-readiness questions to release_agent. A single "
        "request may require more than one specialist; synthesize their tool-grounded findings without "
        "changing them. Always ground answers in tool results, never assume."
    ),
    tools=[tool_query_status],
    sub_agents=[compliance_agent, greenlight_agent, release_agent],
)
