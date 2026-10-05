"""
STEP 5 ONLY: Agent 3 -- Remediation.

This agent's one job: given a diagnosis (root cause + affected services),
write a clear, prioritized action plan for the ops team. It does NOT
re-diagnose anything -- it trusts Agent 2's conclusion and focuses purely
on "what do we DO about it."
"""

import asyncio
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.genai.errors import ServerError

MODEL = "gemini-3.8-flash"
APP_NAME = "network_incident_agent"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 15


remediation_agent = Agent(
    name="remediation_agent",
    model=MODEL,
    instruction="""You are a NOC team lead writing an action plan for the
    operations team. Given a diagnosis (root cause + affected services),
    provide clear, prioritized remediation steps. Format as a short,
    numbered, actionable list -- written for someone who needs to act on
    this immediately, not for someone who needs more analysis.""",
)


async def run_remediation(diagnosis_summary: str):
    runner = InMemoryRunner(agent=remediation_agent, app_name=APP_NAME)

    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="local_test"
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async for event in runner.run_async(
                user_id="local_test",
                session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part(text=diagnosis_summary)]),
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(f"[{event.author}] {part.text}")
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
    # Hardcoded test input -- standing in for Agent 2's real output
    fake_diagnosis_output = """
    Root Cause: An outage in region us-east1 forced a 100% traffic failover
    to us-central1, exhausting CPU capacity on the payment-gateway service
    and causing downstream connection timeouts.

    Affected Services:
    - checkout-api
    - payment-gateway
    """
    print("Running Remediation Agent only (with fake diagnosis input)...\n")
    asyncio.run(run_remediation(fake_diagnosis_output))
