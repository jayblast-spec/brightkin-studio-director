from google.adk.agents import Agent
from agents.tool_wrappers import tool_check_diversity, tool_check_music_policy, tool_check_pacing

compliance_agent = Agent(
    name="compliance_agent",
    model="gemini-flash-lite-latest",
    instruction=(
        "You check BrightKin production items against three standards: "
        "(1) cast diversity - friend_char_white, friend_char_latino, and friend_char_asian must all "
        "have status 'designed'; (2) music originality - a track's provenance must be 'original'; "
        "(3) camera-pacing variety - a scene sequence must use more than one distinct camera_angle. "
        "Call the tool matching the standard the question asks about. If the result has "
        "\"exists\": false, tell the user no such item was found in the production log - do not "
        "describe a nonexistent item as failing compliance. Otherwise state the exact pass/fail "
        "result and the specific gap if it fails. Do not guess at data you have not queried."
    ),
    tools=[tool_check_diversity, tool_check_music_policy, tool_check_pacing],
)
