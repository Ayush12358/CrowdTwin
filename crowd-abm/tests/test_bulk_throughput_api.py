from __future__ import annotations

import unittest

from src.api import simulate_payload_bulk, step_payload_bulk_gpu
from src.core.errors import PayloadFormatError


class BulkThroughputApiTests(unittest.TestCase):
    def test_simulate_payload_bulk_runs_multiple_steps(self) -> None:
        payload = {
            "occupancy": [
                [-1, -1, -1],
                [-1, 1, -1],
                [-1, -1, -1],
            ],
            "agents": [
                {"agent_id": 1, "row": 1, "col": 1, "d_row": 0.0, "d_col": 1.0, "will": 1.0},
            ],
            "metadata": {
                "config_version": "v1",
                "policy_version": "hardcoded-v1",
                "seed": 1,
            },
        }

        out = simulate_payload_bulk(payload, steps=2)
        self.assertEqual(out["occupancy"][1][2], 1)
        self.assertIn("metadata", out)
        self.assertEqual(out["metadata"]["requested_steps"], 2)
        self.assertEqual(out["metadata"]["simulated_steps"], 2)
        self.assertFalse(out["metadata"]["early_converged"])

    def test_simulate_payload_bulk_stops_on_convergence(self) -> None:
        payload = {
            "occupancy": [[1]],
            "agents": [{"agent_id": 1, "row": 0, "col": 0, "d_row": 0.0, "d_col": 0.0, "will": 1.0}],
            "metadata": {
                "config_version": "v1",
                "policy_version": "hardcoded-v1",
                "seed": 1,
            },
        }

        out = simulate_payload_bulk(payload, steps=60)
        self.assertEqual(out["metadata"]["requested_steps"], 60)
        self.assertEqual(out["metadata"]["simulated_steps"], 1)
        self.assertTrue(out["metadata"]["early_converged"])

    def test_simulate_payload_bulk_rejects_non_positive_steps(self) -> None:
        payload = {
            "occupancy": [[1]],
            "agents": [{"agent_id": 1, "row": 0, "col": 0}],
        }

        with self.assertRaises(PayloadFormatError):
            simulate_payload_bulk(payload, steps=0)

    def test_step_payload_bulk_gpu_fallback(self) -> None:
        payload = {
            "occupancy": [[1, -1], [-1, -1]],
            "agents": [{"agent_id": 1, "row": 0, "col": 0, "d_row": 1.0, "d_col": 0.0, "will": 0.9}],
        }

        out = step_payload_bulk_gpu(payload, fallback_to_cpu=True)
        self.assertEqual(out["occupancy"][1][0], 1)


if __name__ == "__main__":
    unittest.main()
