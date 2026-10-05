"""
STEP 4 ONLY: Agent 2 -- Diagnosis.

This agent's one job: given an ALREADY-DETECTED incident summary (from
Agent 1), figure out the root cause and list every affected service.
It does NOT re-fetch raw data -- it reasons over what Detection already found,
the same way a senior engineer reviews a junior's incident report rather
than re-pulling every log themselves.
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


diagnosis_agent = Agent(
    name="diagnosis_agent",
    model=MODEL,
    instruction="""You are a senior network engineer doing root-cause analysis.
    You will receive a summary of a detected incident. Your job is ONLY to:
    1. State the single most likely root cause, in one sentence.
    2. List every affected service, as a bullet list.
    Do not suggest remediation steps -- that is a different team's job.
    Be concise.""",
)


async def run_diagnosis(incident_summary: str):
    runner = InMemoryRunner(agent=diagnosis_agent, app_name=APP_NAME)

    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="local_test"
    )

    # Retry loop: Gemini occasionally returns 503 "high demand" errors that
    # clear up within seconds -- this retries automatically instead of
    # failing the whole run on a temporary blip.
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async for event in runner.run_async(
                user_id="local_test",
                session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part(text=incident_summary)]),
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            print(f"[{event.author}] {part.text}")
            return  # success -- exit the retry loop
        except ServerError as e:
            if attempt < MAX_RETRIES:
                print(f"  (Gemini busy, attempt {attempt}/{MAX_RETRIES} failed -- "
                      f"retrying in {RETRY_DELAY_SECONDS}s...)")
                await asyncio.sleep(RETRY_DELAY_SECONDS)
            else:
                print(f"  Gave up after {MAX_RETRIES} attempts: {e}")
                raise


if __name__ == "__main__":
    # Hardcoded test input for now -- standing in for Agent 1's real output,
    # so we can test Agent 2 completely on its own before chaining them.
    fake_detection_output = """
    Incident detected: checkout-api is experiencing high latency (p99: 4200ms).
    Logs show checkout-api has 10 connection timeouts to payment-gateway in the
    last 5 minutes. payment-gateway CPU is at 95%. Topology shows us-east1 is
    unhealthy, causing 100% traffic failover to us-central1.
    """
    print("Running Diagnosis Agent only (with fake detection input)...\n")
    asyncio.run(run_diagnosis(fake_detection_output))
