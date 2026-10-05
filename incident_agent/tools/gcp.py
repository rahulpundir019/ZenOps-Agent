from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from incident_agent.config import settings


def format_log_entry(entry: Any, max_payload: int = 200) -> str:
    payload = getattr(entry, "payload", "")
    text = str(payload) if payload is not None else ""
    if len(text) > max_payload:
        text = text[:max_payload] + "..."
    severity = getattr(entry, "severity", "DEFAULT")
    timestamp = getattr(entry, "timestamp", "")
    return f"[{severity}] {timestamp} - {text}"


def log_filter(project_id: str, lookback_minutes: int, test_log_name: str) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=lookback_minutes)
    cutoff_iso = cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    log_name = f"projects/{project_id}/logs/{test_log_name}"
    return (
        f'timestamp>="{cutoff_iso}" AND '
        f'(severity>=WARNING OR logName="{log_name}")'
    )


def format_alert_policies(policies: Iterable[Any]) -> str:
    lines = []
    for policy in policies:
        display_name = getattr(policy, "display_name", "unnamed")
        enabled = getattr(policy, "enabled", False)
        lines.append(f"Alert policy: {display_name} (enabled: {enabled})")
    if not lines:
        return (
            "No alert policies configured in this project. "
            "Policy list is not the same as currently firing incidents — "
            "rely on recent error logs if no policies exist."
        )
    header = (
        "Configured Cloud Monitoring alert policies "
        "(definitions only; enabled=true does not mean an incident is firing):\n"
    )
    return header + "\n".join(lines)


def get_recent_alarms() -> str:
    """Pulls configured Cloud Monitoring alert policies."""
    from google.api_core import exceptions as gcp_exceptions
    from google.auth.exceptions import DefaultCredentialsError
    from google.cloud import monitoring_v3

    try:
        client = monitoring_v3.AlertPolicyServiceClient()
        project_name = f"projects/{settings.project_id}"
        policies = client.list_alert_policies(name=project_name)
        return format_alert_policies(policies)
    except DefaultCredentialsError as exc:
        return f"Could not read alert policies: missing GCP credentials ({exc})."
    except gcp_exceptions.GoogleAPICallError as exc:
        return f"Could not read alert policies: {exc}."


def get_recent_logs(limit: int | None = None) -> str:
    """Pulls recent warning+ logs, plus seeded incident test logs."""
    from google.api_core import exceptions as gcp_exceptions
    from google.auth.exceptions import DefaultCredentialsError
    from google.cloud import logging as gcp_logging

    max_results = limit if limit is not None else settings.log_limit
    try:
        client = gcp_logging.Client(project=settings.project_id)
        entries = client.list_entries(
            filter_=log_filter(
                settings.project_id,
                settings.log_lookback_minutes,
                settings.test_log_name,
            ),
            order_by=gcp_logging.DESCENDING,
            max_results=max_results,
        )
        results = [format_log_entry(entry) for entry in entries]
        if not results:
            return (
                "No warning/error (or seeded incident) log entries found in the "
                f"last {settings.log_lookback_minutes} minutes."
            )
        return "\n".join(results)
    except DefaultCredentialsError as exc:
        return f"Could not read logs: missing GCP credentials ({exc})."
    except gcp_exceptions.GoogleAPICallError as exc:
        return f"Could not read logs: {exc}."


def get_network_topology() -> str:
    """Placeholder until Network Intelligence Center is wired in."""
    return (
        "Network topology data is not connected yet. "
        "Infer dependencies only from logs and alarms; do not invent a topology."
    )


GCP_TOOLS = [get_recent_alarms, get_recent_logs, get_network_topology]
