import unittest

from incident_agent.cli import build_parser
from incident_agent.pipeline import build_pipeline


class PipelineWiringTest(unittest.TestCase):
    def test_pipeline_has_three_named_agents(self):
        pipeline = build_pipeline("mock")
        names = [agent.name for agent in pipeline.sub_agents]
        self.assertEqual(
            names, ["detection_agent", "diagnosis_agent", "remediation_agent"]
        )

    def test_detection_uses_mock_tools(self):
        detection = build_pipeline("mock").sub_agents[0]
        self.assertEqual(
            [tool.__name__ for tool in detection.tools],
            ["get_recent_alarms", "get_recent_logs", "get_network_topology"],
        )

    def test_output_keys_chain_state(self):
        detection, diagnosis, remediation = build_pipeline("gcp").sub_agents
        self.assertEqual(detection.output_key, "detection_summary")
        self.assertEqual(diagnosis.output_key, "diagnosis_summary")
        self.assertEqual(remediation.output_key, "remediation_plan")
        self.assertIn("{detection_summary}", diagnosis.instruction)
        self.assertIn("{diagnosis_summary}", remediation.instruction)


class CliTest(unittest.TestCase):
    def test_run_defaults_to_mock(self):
        args = build_parser().parse_args(["run"])
        self.assertEqual(args.source, "mock")

    def test_run_accepts_gcp_source(self):
        args = build_parser().parse_args(["run", "--source", "gcp"])
        self.assertEqual(args.source, "gcp")


if __name__ == "__main__":
    unittest.main()
