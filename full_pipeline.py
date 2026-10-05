"""
STEP 6: The full 3-agent pipeline, chained together for real.

Detection -> Diagnosis -> Remediation, with each agent's REAL output
automatically feeding the next one. SequentialAgent handles the handoff --
we don't manually copy text between agents anymore.
"""

import asyncio
from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.genai.errors import ServerError

MODEL = "gemini-3.1-flash-lite"
APP_NAME = "network_incident_agent"
MAX_RETRIES = 4           # bumped up -- we've seen real demand spikes testing this
RETRY_DELAY_SECONDS = 15


# ----- MOCK DATA TOOLS (Agent 1 only) -----
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


# ----- THE THREE AGENTS -----
detection_agent = Agent(
    name="detection_agent",
    model=MODEL,
    instruction="""You are a network monitoring engineer. Look at alarms,
    logs, and topology data, and determine if there is a real incident
    happening. Summarize what you found clearly and concisely. Call the
    tools provided to gather data before concluding anything.""",
    tools=[get_recent_alarms, get_recent_logs, get_network_topology],
)

diagnosis_agent = Agent(
    name="diagnosis_agent",
    model=MODEL,
    instruction="""You are a senior network engineer doing root-cause analysis.
    You will receive a summary of a detected incident. State the single most
    likely root cause in one sentence, then list every affected service as a
    bullet list. Do not suggest remediation steps. Be concise.""",
)

remediation_agent = Agent(
    name="remediation_agent",
    model=MODEL,
    instruction="""You are a NOC team lead writing an action plan for the
    operations team. Given a diagnosis, provide clear, prioritized
    remediation steps as a short numbered list -- written for someone who
    needs to act immediately.""",
)

# SequentialAgent runs sub_agents in order, automatically passing each
# agent's output as the next agent's input. This is the actual "chaining"
# -- no manual copy-pasting of text between agents like our test scripts did.
network_incident_pipeline = SequentialAgent(
    name="network_incident_pipeline",
    sub_agents=[detection_agent, diagnosis_agent, remediation_agent],
)


async def run_pipeline(user_trigger: str):
    runner = InMemoryRunner(agent=network_incident_pipeline, app_name=APP_NAME)

    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="local_test"
    )

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
                print(f"  (Gemini busy, attempt {attempt}/{MAX_RETRIES} failed -- "
                      f"retrying in {RETRY_DELAY_SECONDS}s...)")
                await asyncio.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"  Gave up after {MAX_RETRIES} attempts: {e}")
                raise


if __name__ == "__main__":
    print("Running FULL 3-agent pipeline...\n")
    asyncio.run(run_pipeline("Check current network health and report any incidents."))
