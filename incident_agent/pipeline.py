from __future__ import annotations

from google.adk.agents import SequentialAgent

from incident_agent.agents import (
    DEFAULT_TRIGGER,
    build_detection_agent,
    build_diagnosis_agent,
    build_remediation_agent,
)
from incident_agent.result import PipelineResult
from incident_agent.runner import run_agent
from incident_agent.tools.gcp import GCP_TOOLS
from incident_agent.tools.mock import MOCK_TOOLS


def build_pipeline(source: str = "mock") -> SequentialAgent:
    tools = MOCK_TOOLS if source == "mock" else GCP_TOOLS
    return SequentialAgent(
        name="network_incident_pipeline",
        sub_agents=[
            build_detection_agent(tools),
            build_diagnosis_agent(),
            build_remediation_agent(),
        ],
    )


async def run_pipeline(
    user_trigger: str = DEFAULT_TRIGGER,
    *,
    source: str = "mock",
) -> PipelineResult:
    if source not in {"mock", "gcp"}:
        raise ValueError("source must be 'mock' or 'gcp'")
    return await run_agent(build_pipeline(source), user_trigger)
