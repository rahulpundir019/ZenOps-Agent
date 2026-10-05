from __future__ import annotations

from incident_agent.config import settings


def seed_test_incident() -> list[tuple[str, str]]:
    """Write synthetic-but-real Cloud Logging entries that mimic an outage."""
    import google.cloud.logging as gcp_logging

    client = gcp_logging.Client(project=settings.project_id)
    logger = client.logger(settings.test_log_name)
    entries = [
        (
            "ERROR",
            "checkout-api: Connection timeout to payment-gateway (10 occurrences, last 5 min)",
        ),
        ("WARNING", "payment-gateway: CPU usage at 95%"),
        (
            "WARNING",
            "load-balancer: routing 100% traffic to us-central1 (us-east1 unhealthy)",
        ),
        (
            "CRITICAL",
            "checkout-api: p99 latency at 4200ms, threshold 500ms exceeded",
        ),
    ]
    for severity, message in entries:
        logger.log_text(message, severity=severity)
    return entries
