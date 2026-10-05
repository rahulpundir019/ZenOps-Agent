"""
STEP 3 ONLY: Agent 1 -- Detection.

This agent's one job: look at alarms, logs, and topology data, and decide
whether there's a real incident happening.
"""

import asyncio
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

MODEL = "gemini-3.8-flash"
APP_NAME = "network_incident_agent"  # must stay consistent everywhere


# ----- MOCK DATA TOOLS -----
def get_recent_alarms() -> str:
    """Returns recent monitoring alarms (mocked)."""
    return """
    ALARM: High latency on service 'checkout-api' (p99: 4200ms, threshold: 500ms)
    Triggered: 2 minutes ago
    Region: us-central1
    """


def get_recent_logs() -> str:
    """Returns recent error/warning logs (mocked)."""
    return """
    [ERROR] checkout-api: Connection timeout to payment-gateway (10 occurrences, last 5 min)
    [WARN]  payment-gateway: CPU usage at 95%
    [INFO]  load-balancer: routing 100% traffic to us-central1 (us-east1 unhealthy)
    """


def get_network_topology() -> str:
    """Returns service dependency topology (mocked)."""
    return """
    checkout-api depends on: payment-gateway, inventory-service
    payment-gateway depends on: external-bank-api
    Current known-unhealthy nodes: us-east1 region (load balancer failover active)
    """


# ----- THE AGENT -----
detection_agent = Agent(
    name="detection_agent",
    model=MODEL,
    instruction="""You are a network monitoring engineer. Your job: look at
    alarms, logs, and topology data, and determine if there is a real
    incident happening. Summarize what you found clearly and concisely.
    Call the tools provided to gather data before concluding anything.""",
    tools=[get_recent_alarms, get_recent_logs, get_network_topology],
)


# ----- RUN IT (async version -- this is the fix) -----
async def run_detection(user_trigger: str):
    runner = InMemoryRunner(agent=detection_agent, app_name=APP_NAME)

    # await, not create_session_sync -- this is the part that was broken
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="local_test"
    )

    async for event in runner.run_async(
        user_id="local_test",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=user_trigger)]),
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    print(f"[{event.author}] {part.text}")
                if part.function_call:
                    print(f"[{event.author}] CALLING TOOL: {part.function_call.name}")
                if part.function_response:
                    print(f"[{event.author}] TOOL RESULT: {part.function_response.response}")


if __name__ == "__main__":
    print("Running Detection Agent only...\n")
    asyncio.run(run_detection("Check current network health and report any incidents."))
