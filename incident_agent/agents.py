from __future__ import annotations

from collections.abc import Callable, Sequence

from google.adk.agents import Agent

from incident_agent.config import settings

ToolFn = Callable[..., str]


DETECTION_INSTRUCTION = """You are a network monitoring engineer.
Look at alarms, logs, and topology data, and determine if there is a real incident.

Rules:
- Call the tools provided before concluding anything.
- If the data shows no alarms and only routine admin activity, say clearly that
  no incident is detected. Do not invent an incident.
- Summarize what you found clearly and concisely.
"""

DIAGNOSIS_INSTRUCTION = """You are a senior network engineer doing root-cause analysis.
Use the detection summary below if present; otherwise use the user message.

Detection summary:
{detection_summary}

Rules:
- If no real incident was detected, say so briefly and stop. Do not fabricate a root cause.
- If an incident WAS detected: state the single most likely root cause in one sentence,
  then list every affected service as a bullet list.
- Do not suggest remediation steps.
- Be concise.
"""

REMEDIATION_INSTRUCTION = """You are a NOC team lead writing an action plan.
Use the diagnosis below if present; otherwise use the user message.

Diagnosis:
{diagnosis_summary}

Rules:
- If no incident was diagnosed, confirm no action is needed.
- If an incident was diagnosed, provide clear, prioritized remediation steps as a
  short numbered list for someone who must act immediately.
"""

FAKE_DETECTION_OUTPUT = """
Incident detected: checkout-api is experiencing high latency (p99: 4200ms).
Logs show checkout-api has 10 connection timeouts to payment-gateway in the
last 5 minutes. payment-gateway CPU is at 95%. Topology shows us-east1 is
unhealthy, causing 100% traffic failover to us-central1.
""".strip()

FAKE_DIAGNOSIS_OUTPUT = """
Root Cause: An outage in region us-east1 forced a 100% traffic failover
to us-central1, exhausting CPU capacity on the payment-gateway service
and causing downstream connection timeouts.

Affected Services:
- checkout-api
- payment-gateway
""".strip()

DEFAULT_TRIGGER = "Check current network health and report any incidents."


def build_detection_agent(tools: Sequence[ToolFn]) -> Agent:
    return Agent(
        name="detection_agent",
        model=settings.model,
        instruction=DETECTION_INSTRUCTION,
        tools=list(tools),
        output_key="detection_summary",
    )


def build_diagnosis_agent() -> Agent:
    return Agent(
        name="diagnosis_agent",
        model=settings.model,
        instruction=DIAGNOSIS_INSTRUCTION,
        output_key="diagnosis_summary",
    )


def build_remediation_agent() -> Agent:
    return Agent(
        name="remediation_agent",
        model=settings.model,
        instruction=REMEDIATION_INSTRUCTION,
        output_key="remediation_plan",
    )
