from __future__ import annotations

import unittest

from src.api import step_payload, step_payload_bulk
from src.core.errors import PayloadFormatError


class BulkApiTests(unittest.TestCase):
    def test_bulk_matches_reference_on_small_payload(self) -> None:
        payload = {
            "occupancy": [
                [1, -1, -1, -1],
                [-1, -1, -1, -1],
                [-1, -1, 2, -1],
                [-1, -1, -1, 3],
            ],
            "agents": [
                {"agent_id": 1, "row": 0, "col": 0, "d_row": 1.0, "d_col": 1.0, "will": 0.9},
                {"agent_id": 2, "row": 2, "col": 2, "d_row": 0.0, "d_col": -1.0, "will": 0.8},
                {"agent_id": 3, "row": 3, "col": 3, "d_row": -1.0, "d_col": -1.0, "will": 0.7},
            ],
        }

        reference = step_payload(payload)
        bulk = step_payload_bulk(payload)

        self.assertEqual(reference["occupancy"], bulk["occupancy"])
        self.assertEqual(reference["diagnostics"]["moved_count"], bulk["diagnostics"]["moved_count"])
        self.assertEqual(reference["diagnostics"]["blocked_count"], bulk["diagnostics"]["blocked_count"])
        self.assertEqual(reference["diagnostics"]["conflict_count"], bulk["diagnostics"]["conflict_count"])
        self.assertEqual(reference["diagnostics"]["tie_break_count"], bulk["diagnostics"]["tie_break_count"])
        self.assertAlmostEqual(
            reference["diagnostics"]["avg_displacement"],
            bulk["diagnostics"]["avg_displacement"],
        )
        self.assertAlmostEqual(
            reference["diagnostics"]["avg_winner_will"],
            bulk["diagnostics"]["avg_winner_will"],
        )

        ref_agents = sorted(reference["agents"], key=lambda a: a["agent_id"])
        bulk_agents = sorted(bulk["agents"], key=lambda a: a["agent_id"])
        self.assertEqual(ref_agents, bulk_agents)

    def test_bulk_conflict_resolution_tie_break(self) -> None:
        payload = {
            "occupancy": [
                [-1, -1, -1],
                [1, -1, 2],
                [-1, -1, -1],
            ],
            "agents": [
                {"agent_id": 1, "row": 1, "col": 0, "d_row": 0.0, "d_col": 1.0, "will": 0.5},
                {"agent_id": 2, "row": 1, "col": 2, "d_row": 0.0, "d_col": -1.0, "will": 0.5},
            ],
        }

        out = step_payload_bulk(payload)

        self.assertEqual(out["occupancy"][1][1], 1)
        self.assertEqual(out["occupancy"][1][2], 2)
        self.assertEqual(out["diagnostics"]["conflict_count"], 1)
        self.assertEqual(out["diagnostics"]["tie_break_count"], 1)

    def test_bulk_rejects_out_of_bounds(self) -> None:
        payload = {
            "occupancy": [[-1, -1], [-1, -1]],
            "agents": [{"agent_id": 1, "row": 3, "col": 0, "d_row": 0.0, "d_col": 0.0}],
        }

        with self.assertRaises(PayloadFormatError):
            step_payload_bulk(payload)

    def test_bulk_columnar_output(self) -> None:
        payload = {
            "occupancy": [[1, -1], [-1, -1]],
            "agents": [{"agent_id": 1, "row": 0, "col": 0, "d_row": 1.0, "d_col": 0.0, "will": 0.7}],
            "columnar_output": True,
        }

        out = step_payload_bulk(payload)
        self.assertIsInstance(out["agents"], dict)
        self.assertEqual(out["agents"]["agent_id"], [1])
        self.assertEqual(out["agents"]["row"], [1])
        self.assertEqual(out["agents"]["col"], [0])


if __name__ == "__main__":
    unittest.main()
