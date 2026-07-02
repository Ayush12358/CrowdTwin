from __future__ import annotations

import unittest

from src.api import step
from src.core.state import AgentState, SimState
from src.core.terrain import build_default_terrain
from src.core.validators import build_occupancy


class GoldenRegressionTests(unittest.TestCase):
    def test_three_agent_conflict_and_boundary_golden(self) -> None:
        # Golden scenario covers boundary block, conflict winner, and one diagonal move.
        agents = {
            1: AgentState(agent_id=1, row=0, col=0, d_row=-1.0, d_col=0.0, will=0.2),
            2: AgentState(agent_id=2, row=2, col=1, d_row=0.0, d_col=1.0, will=0.9),
            3: AgentState(agent_id=3, row=1, col=2, d_row=1.0, d_col=0.0, will=0.6),
            4: AgentState(agent_id=4, row=3, col=3, d_row=-1.0, d_col=-1.0, will=0.5),
        }
        state = SimState(
            occupancy=build_occupancy((5, 5), agents),
            terrain=build_default_terrain((5, 5)),
            agents=agents,
        )

        result = step(state)

        expected_occupancy = [
            [1, -1, -1, -1, -1],
            [-1, -1, 3, -1, -1],
            [-1, -1, 2, -1, -1],
            [-1, -1, -1, 4, -1],
            [-1, -1, -1, -1, -1],
        ]

        self.assertEqual(result.state.occupancy, expected_occupancy)
        self.assertEqual(result.diagnostics.moved_count, 1)
        self.assertEqual(result.diagnostics.blocked_count, 3)
        self.assertEqual(result.diagnostics.conflict_count, 1)
        self.assertEqual(result.diagnostics.tie_break_count, 0)
        self.assertAlmostEqual(result.diagnostics.avg_winner_will, 0.9)


if __name__ == "__main__":
    unittest.main()
