"""
STEP 6: Real GCP data tools -- these replace the mocked get_recent_alarms,
get_recent_logs, and get_network_topology functions from before.

Run this file on its own first, separately from the agents, to confirm
the GCP connection and auth actually work before wiring it into Agent 1.
"""

from google.cloud import monitoring_v3
from google.cloud import logging as gcp_logging

PROJECT_ID = "network-incident-agent"


def get_recent_alarms() -> str:
    """Pulls active alert incidents from Cloud Monitoring."""
    client = monitoring_v3.AlertPolicyServiceClient()
    project_name = f"projects/{PROJECT_ID}"

    policies = client.list_alert_policies(name=project_name)
    results = []
    for policy in policies:
        results.append(f"Alert policy: {policy.display_name} (enabled: {policy.enabled})")

    if not results:
        return "No alert policies configured in this project."
    return "\n".join(results)


def get_recent_logs(limit: int = 20) -> str:
    """Pulls the most recent log entries from Cloud Logging."""
    client = gcp_logging.Client(project=PROJECT_ID)

    entries = client.list_entries(
        order_by=gcp_logging.DESCENDING,
        max_results=limit,
    )

    results = []
    for entry in entries:
        results.append(f"[{entry.severity}] {entry.timestamp} - {entry.payload}")

    if not results:
        return "No recent log entries found in this project."
    return "\n".join(results)


def get_network_topology() -> str:
    """
    Placeholder for Network Intelligence Center data.
    This API is more involved to query programmatically -- for now, this
    stays descriptive text. We'll wire in the real topology API as a
    follow-up step once alarms + logs are confirmed working.
    """
    return "Network topology data not yet connected -- using placeholder."


if __name__ == "__main__":
    print("--- Testing get_recent_alarms() ---")
    print(get_recent_alarms())
    print("\n--- Testing get_recent_logs() ---")
    print(get_recent_logs())
    print("\n--- Testing get_network_topology() ---")
    print(get_network_topology())
