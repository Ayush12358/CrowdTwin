from __future__ import annotations

import unittest

from src.api import step_payload


class PayloadIntegrationTests(unittest.TestCase):
    def _assert_output_consistent(self, output: dict[str, object]) -> None:
        occupancy = output["occupancy"]
        agents = output["agents"]
        diagnostics = output["diagnostics"]

        self.assertIsInstance(occupancy, list)
        self.assertGreater(len(occupancy), 0)
        self.assertIsInstance(agents, list)

        rows = len(occupancy)
        cols = len(occupancy[0])
        self.assertGreater(cols, 0)

        agent_positions = {}
        for raw_agent in agents:
            self.assertIsInstance(raw_agent, dict)
            agent_id = int(raw_agent["agent_id"])
            row = int(raw_agent["row"])
            col = int(raw_agent["col"])
            self.assertTrue(0 <= row < rows)
            self.assertTrue(0 <= col < cols)
            self.assertNotIn((row, col), agent_positions.values())
            agent_positions[agent_id] = (row, col)

        self.assertEqual(diagnostics["moved_count"] + diagnostics["blocked_count"], len(agents))

        for agent_id, (row, col) in agent_positions.items():
            self.assertEqual(occupancy[row][col], agent_id)

        cells_from_occupancy = set()
        for row_idx, row in enumerate(occupancy):
            self.assertEqual(len(row), cols)
            for col_idx, value in enumerate(row):
                self.assertIsInstance(value, int)
                if value != -1:
                    cells_from_occupancy.add((row_idx, col_idx, value))
                    self.assertIn(value, agent_positions)

        self.assertEqual(len(cells_from_occupancy), len(agent_positions))

    def test_orchestrator_style_payload_batch(self) -> None:
        payloads = [
            {
                "occupancy": [
                    [1, -1, -1, -1, -1],
                    [-1, -1, -1, -1, -1],
                    [-1, -1, 2, -1, -1],
                    [-1, -1, -1, 3, -1],
                    [-1, -1, -1, -1, 4],
                ],
                "agents": [
                    {"agent_id": 1, "row": 0, "col": 0, "d_row": 1.0, "d_col": 1.0, "will": 0.9},
                    {"agent_id": 2, "row": 2, "col": 2, "d_row": 0.0, "d_col": -1.0, "will": 0.8},
                    {"agent_id": 3, "row": 3, "col": 3, "d_row": -1.0, "d_col": 0.0, "will": 0.7},
                    {"agent_id": 4, "row": 4, "col": 4, "d_row": -1.0, "d_col": -1.0, "will": 0.6},
                ],
                "metadata": {
                    "config_version": "mvp-v1",
                    "policy_version": "hardcoded-v1",
                    "seed": 123,
                    "map_version": "grid-a",
                    "run_id": "batch-1",
                },
            },
            {
                "occupancy": [
                    [-1, -1, -1, -1, -1],
                    [-1, 1, -1, -1, -1],
                    [-1, -1, 2, -1, -1],
                    [-1, -1, -1, 3, -1],
                    [-1, -1, -1, -1, 4],
                ],
                "agents": [
                    {"agent_id": 1, "row": 1, "col": 1, "d_row": 0.0, "d_col": 1.0, "will": 0.9},
                    {"agent_id": 2, "row": 2, "col": 2, "d_row": 1.0, "d_col": 0.0, "will": 0.8},
                    {"agent_id": 3, "row": 3, "col": 3, "d_row": -1.0, "d_col": -1.0, "will": 0.7},
                    {"agent_id": 4, "row": 4, "col": 4, "d_row": -1.0, "d_col": 0.0, "will": 0.6},
                ],
                "metadata": {
                    "config_version": "mvp-v1",
                    "policy_version": "hardcoded-v1",
                    "seed": 123,
                    "map_version": "grid-a",
                    "run_id": "batch-2",
                },
            },
        ]

        outputs = [
            step_payload(payload, include_events=True, include_metadata=True)
            for payload in payloads
        ]

        for index, output in enumerate(outputs):
            with self.subTest(index=index):
                self._assert_output_consistent(output)
                self.assertIn("events", output)
                self.assertEqual(len(output["events"]), len(output["agents"]))
                self.assertEqual(output["metadata"]["policy_version"], "hardcoded-v1")

    def test_payload_batch_replay_is_deterministic(self) -> None:
        payload = {
            "occupancy": [
                [-1, -1, -1],
                [-1, 1, 2],
                [-1, -1, -1],
            ],
            "agents": [
                {"agent_id": 1, "row": 1, "col": 1, "d_row": 0.0, "d_col": 1.0, "will": 0.6},
                {"agent_id": 2, "row": 1, "col": 2, "d_row": 0.0, "d_col": -1.0, "will": 0.8},
            ],
            "metadata": {
                "config_version": "mvp-v1",
                "policy_version": "hardcoded-v1",
                "seed": 42,
                "map_version": "grid-b",
                "run_id": "determinism",
            },
        }

        first = step_payload(payload, include_events=True, include_metadata=True)
        second = step_payload(payload, include_events=True, include_metadata=True)

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
