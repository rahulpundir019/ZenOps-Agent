"""
STEP 7: Full 3-agent pipeline, now using REAL GCP data for alarms and logs
(topology stays a placeholder for now -- that API is more involved).
"""

import asyncio
from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.genai.errors import ServerError
from google.cloud import monitoring_v3
from google.cloud import logging as gcp_logging

MODEL = "gemini-3.1-flash-lite"
APP_NAME = "network_incident_agent"
PROJECT_ID = "network-incident-agent"
MAX_RETRIES = 4
RETRY_DELAY_SECONDS = 15


# ----- REAL GCP DATA TOOLS -----
def get_recent_alarms() -> str:
    """Pulls active alert policies from Cloud Monitoring."""
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{PROJECT_ID}"
    policies = client.list_alert_policies(name=project_name)
    results = [f"Alert policy: {p.display_name} (enabled: {p.enabled})" for p in policies]
    return "\n".join(results) if results else "No alert policies configured in this project."


def get_recent_logs(limit: int = 20) -> str:
    """Pulls the most recent log entries from Cloud Logging."""
    client = gcp_logging.Client(project=PROJECT_ID)
    entries = client.list_entries(order_by=gcp_logging.DESCENDING, max_results=limit)
    results = [f"[{e.severity}] {e.timestamp} - {str(e.payload)[:200]}" for e in entries]
    return "\n".join(results) if results else "No recent log entries found in this project."


def get_network_topology() -> str:
    """Placeholder -- Network Intelligence Center integration comes later."""
    return "Network topology data not yet connected -- using placeholder."


# ----- THE THREE AGENTS (unchanged from before) -----
detection_agent = Agent(
    name="detection_agent",
    model=MODEL,
    instruction="""You are a network monitoring engineer. Look at alarms,
    logs, and topology data, and determine if there is a real incident
    happening. If the data shows no alarms and only routine admin activity
    in the logs, say clearly that no incident is detected -- do not invent
    one. Summarize what you found concisely. Call the tools provided to
    gather data before concluding anything.""",
    tools=[get_recent_alarms, get_recent_logs, get_network_topology],
)

diagnosis_agent = Agent(
    name="diagnosis_agent",
    model=MODEL,
    instruction="""You are a senior network engineer doing root-cause analysis.
    You will receive a summary from the detection step. If no real incident
    was detected, say so briefly and stop -- do not fabricate a root cause.
    If an incident WAS detected, state the most likely root cause in one
    sentence, then list affected services. Be concise.""",
)

remediation_agent = Agent(
    name="remediation_agent",
    model=MODEL,
    instruction="""You are a NOC team lead. If no incident was diagnosed,
    simply confirm no action is needed. If an incident was diagnosed,
    provide clear, prioritized remediation steps as a numbered list.""",
)

network_incident_pipeline = SequentialAgent(
    name="network_incident_pipeline",
    sub_agents=[detection_agent, diagnosis_agent, remediation_agent],
)


async def run_pipeline(user_trigger: str):
    runner = InMemoryRunner(agent=network_incident_pipeline, app_name=APP_NAME)
    session = await runner.session_service.create_session(app_name=APP_NAME, user_id="local_test")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async for event in runner.run_async(
                user_id="local_test",
                session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part(text=user_trigger)]),
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(f"\n--- [{event.author}] ---\n{part.text}")
                        if part.function_call:
                            print(f"[{event.author}] CALLING TOOL: {part.function_call.name}")
            return
        except ServerError as e:
            if attempt < MAX_RETRIES:
                print(f"  (Gemini busy, attempt {attempt}/{MAX_RETRIES} failed -- retrying in {RETRY_DELAY_SECONDS}s...)")
                await asyncio.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"  Gave up after {MAX_RETRIES} attempts: {e}")
                raise


if __name__ == "__main__":
    print("Running FULL 3-agent pipeline with REAL GCP data...\n")
    asyncio.run(run_pipeline("Check current network health using real GCP data and report any incidents."))
