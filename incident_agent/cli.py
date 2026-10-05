from __future__ import annotations

import argparse
import asyncio

from incident_agent.agents import (
    DEFAULT_TRIGGER,
    FAKE_DETECTION_OUTPUT,
    FAKE_DIAGNOSIS_OUTPUT,
    build_detection_agent,
    build_diagnosis_agent,
    build_remediation_agent,
)
from incident_agent.pipeline import run_pipeline
from incident_agent.runner import run_agent
from incident_agent.seed import seed_test_incident
from incident_agent.tools.gcp import GCP_TOOLS, get_network_topology, get_recent_alarms, get_recent_logs
from incident_agent.tools.mock import MOCK_TOOLS


def _tools(source: str):
    return MOCK_TOOLS if source == "mock" else GCP_TOOLS


async def _cmd_run(args: argparse.Namespace) -> None:
    label = "MOCK" if args.source == "mock" else "REAL GCP"
    print(f"Running 3-agent pipeline with {label} data...\n")
    await run_pipeline(args.prompt, source=args.source)


async def _cmd_detect(args: argparse.Namespace) -> None:
    print("Running Detection Agent...\n")
    await run_agent(build_detection_agent(_tools(args.source)), args.prompt)


async def _cmd_diagnose(args: argparse.Namespace) -> None:
    print("Running Diagnosis Agent...\n")
    await run_agent(build_diagnosis_agent(), args.prompt)


async def _cmd_remediate(args: argparse.Namespace) -> None:
    print("Running Remediation Agent...\n")
    await run_agent(build_remediation_agent(), args.prompt)


def _cmd_seed(_: argparse.Namespace) -> None:
    from incident_agent.config import settings

    print(f"Writing test log entries to project '{settings.project_id}'...")
    for severity, message in seed_test_incident():
        print(f"  Wrote [{severity}] {message}")
    print("\nDone. Wait ~10s if the pipeline does not see them immediately.")


def _cmd_probe(_: argparse.Namespace) -> None:
    print("--- get_recent_alarms() ---")
    print(get_recent_alarms())
    print("\n--- get_recent_logs() ---")
    print(get_recent_logs())
    print("\n--- get_network_topology() ---")
    print(get_network_topology())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="incident_agent",
        description="Detect, diagnose, and remediate network incidents with ADK agents.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the full detection → diagnosis → remediation pipeline")
    run.add_argument("--source", choices=("mock", "gcp"), default="mock")
    run.add_argument("--prompt", default=DEFAULT_TRIGGER)
    run.set_defaults(handler=lambda args: asyncio.run(_cmd_run(args)))

    detect = sub.add_parser("detect", help="Run only the detection agent")
    detect.add_argument("--source", choices=("mock", "gcp"), default="mock")
    detect.add_argument("--prompt", default=DEFAULT_TRIGGER)
    detect.set_defaults(handler=lambda args: asyncio.run(_cmd_detect(args)))

    diagnose = sub.add_parser("diagnose", help="Run only the diagnosis agent")
    diagnose.add_argument("--prompt", default=FAKE_DETECTION_OUTPUT)
    diagnose.set_defaults(handler=lambda args: asyncio.run(_cmd_diagnose(args)))

    remediate = sub.add_parser("remediate", help="Run only the remediation agent")
    remediate.add_argument("--prompt", default=FAKE_DIAGNOSIS_OUTPUT)
    remediate.set_defaults(handler=lambda args: asyncio.run(_cmd_remediate(args)))

    seed = sub.add_parser("seed", help="Write sample incident logs to Cloud Logging")
    seed.set_defaults(handler=_cmd_seed)

    probe = sub.add_parser("probe-gcp", help="Print raw GCP tool output without running agents")
    probe.set_defaults(handler=_cmd_probe)

    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
