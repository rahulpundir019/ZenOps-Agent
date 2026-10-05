MOCK_ALARMS = """
ALARM: High latency on service 'checkout-api' (p99: 4200ms, threshold: 500ms)
Triggered: 2 minutes ago
Region: us-central1
""".strip()

MOCK_LOGS = """
[ERROR] checkout-api: Connection timeout to payment-gateway (10 occurrences, last 5 min)
[WARN]  payment-gateway: CPU usage at 95%
[INFO]  load-balancer: routing 100% traffic to us-central1 (us-east1 unhealthy)
""".strip()

MOCK_TOPOLOGY = """
checkout-api depends on: payment-gateway, inventory-service
payment-gateway depends on: external-bank-api
Current known-unhealthy nodes: us-east1 region (load balancer failover active)
""".strip()


def get_recent_alarms() -> str:
    """Returns recent monitoring alarms (mocked)."""
    return MOCK_ALARMS


def get_recent_logs() -> str:
    """Returns recent error/warning logs (mocked)."""
    return MOCK_LOGS


def get_network_topology() -> str:
    """Returns service dependency topology (mocked)."""
    return MOCK_TOPOLOGY


MOCK_TOOLS = [get_recent_alarms, get_recent_logs, get_network_topology]
