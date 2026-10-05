import unittest
from types import SimpleNamespace

from incident_agent.tools.gcp import format_alert_policies, format_log_entry, log_filter
from incident_agent.tools.mock import MOCK_ALARMS, get_recent_alarms, get_recent_logs


class MockToolsTest(unittest.TestCase):
    def test_alarms_mention_checkout_latency(self):
        text = get_recent_alarms()
        self.assertIn("checkout-api", text)
        self.assertIn("4200ms", text)
        self.assertEqual(text, MOCK_ALARMS)

    def test_logs_include_payment_gateway_cpu(self):
        self.assertIn("payment-gateway", get_recent_logs())


class GcpFormattersTest(unittest.TestCase):
    def test_format_log_entry_truncates_payload(self):
        entry = SimpleNamespace(
            severity="ERROR",
            timestamp="2026-10-05T00:00:00Z",
            payload="x" * 250,
        )
        line = format_log_entry(entry, max_payload=20)
        self.assertTrue(line.startswith("[ERROR]"))
        self.assertTrue(line.endswith("..."))
        self.assertIn("x" * 20, line)

    def test_format_alert_policies_empty(self):
        text = format_alert_policies([])
        self.assertIn("No alert policies", text)

    def test_format_alert_policies_enabled_flag(self):
        policies = [SimpleNamespace(display_name="High latency", enabled=True)]
        text = format_alert_policies(policies)
        self.assertIn("High latency", text)
        self.assertIn("enabled: True", text)
        self.assertIn("definitions only", text)

    def test_log_filter_includes_lookback_and_seed_log(self):
        filt = log_filter("network-incident-agent", 30, "network-incident-test-log")
        self.assertIn("severity>=WARNING", filt)
        self.assertIn("projects/network-incident-agent/logs/network-incident-test-log", filt)
        self.assertIn("timestamp>=", filt)


if __name__ == "__main__":
    unittest.main()
