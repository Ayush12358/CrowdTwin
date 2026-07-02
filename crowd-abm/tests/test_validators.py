from __future__ import annotations

import unittest

from src.core.errors import OccupancyStateMismatchError, TerrainShapeError, TerrainValueError
from src.core.state import AgentState, SimState
from src.core.terrain import build_default_terrain
from src.core.validators import build_occupancy, validate_state


class ValidatorTests(unittest.TestCase):
    def test_validate_state_passes_for_consistent_input(self) -> None:
        agents = {
            1: AgentState(agent_id=1, row=1, col=1),
            2: AgentState(agent_id=2, row=2, col=3),
        }
        occupancy = build_occupancy((5, 5), agents)
        terrain = build_default_terrain((5, 5))

        state = SimState(occupancy=occupancy, terrain=terrain, agents=agents)
        validate_state(state)

    def test_validate_state_rejects_inconsistent_occupancy(self) -> None:
        agents = {
            1: AgentState(agent_id=1, row=1, col=1),
        }
        occupancy = [[-1, -1, -1, -1] for _ in range(4)]
        terrain = build_default_terrain((4, 4))
        occupancy[0][0] = 1

        state = SimState(occupancy=occupancy, terrain=terrain, agents=agents)

        with self.assertRaises(OccupancyStateMismatchError):
            validate_state(state)

    def test_validate_state_rejects_terrain_shape_mismatch(self) -> None:
        agents = {1: AgentState(agent_id=1, row=0, col=0)}
        occupancy = build_occupancy((2, 2), agents)
        terrain = [[-1], [-1]]

        with self.assertRaises(TerrainShapeError):
            validate_state(SimState(occupancy=occupancy, terrain=terrain, agents=agents))

    def test_validate_state_rejects_invalid_terrain_tile(self) -> None:
        agents = {1: AgentState(agent_id=1, row=0, col=0)}
        occupancy = build_occupancy((2, 2), agents)
        terrain = build_default_terrain((2, 2))
        terrain[1][1] = 9

        with self.assertRaises(TerrainValueError):
            validate_state(SimState(occupancy=occupancy, terrain=terrain, agents=agents))


if __name__ == "__main__":
    unittest.main()
