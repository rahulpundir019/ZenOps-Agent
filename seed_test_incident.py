"""
STEP 8: Writes REAL log entries into Cloud Logging, simulating an incident.

This is NOT mocking the agent's tools -- get_recent_logs() stays 100% real.
We're just making sure there's something genuine in Cloud Logging for it
to find, the same way a real outage would leave real log entries behind.

Run this once before running full_pipeline_real_data.py.
"""

import google.cloud.logging as gcp_logging

PROJECT_ID = "network-incident-agent"

client = gcp_logging.Client(project=PROJECT_ID)
logger = client.logger("network-incident-test-log")

# Each of these becomes a REAL entry in Cloud Logging -- same system your
# get_recent_logs() tool reads from, nothing simulated at the agent level.
test_entries = [
    ("ERROR", "checkout-api: Connection timeout to payment-gateway (10 occurrences, last 5 min)"),
    ("WARNING", "payment-gateway: CPU usage at 95%"),
    ("INFO", "load-balancer: routing 100% traffic to us-central1 (us-east1 unhealthy)"),
    ("CRITICAL", "checkout-api: p99 latency at 4200ms, threshold 500ms exceeded"),
]

print(f"Writing {len(test_entries)} test log entries to project '{PROJECT_ID}'...")
for severity, message in test_entries:
    logger.log_text(message, severity=severity)
    print(f"  Wrote [{severity}] {message}")

print("\nDone. These are now real entries in Cloud Logging.")
print("Note: it can take a few seconds for new entries to become queryable --")
print("if full_pipeline_real_data.py doesn't see them immediately, wait ~10s and retry.")
