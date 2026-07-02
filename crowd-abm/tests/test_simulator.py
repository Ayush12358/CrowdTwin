from __future__ import annotations

import unittest
from typing import Dict

from src.api import step
from src.core.simulator import quantize_intent
from src.core.terrain import TILE_WALL, build_default_terrain
from src.core.state import AgentState, SimState
from src.core.validators import build_occupancy
from src.movement.policy import Intent, Policy


class StaticIntentPolicy(Policy):
    def __init__(self, intents: Dict[int, Intent]) -> None:
        self._intents = intents

    def compute_intents(self, state: SimState) -> Dict[int, Intent]:
        return self._intents


def make_state(shape: tuple[int, int], agents: Dict[int, AgentState]) -> SimState:
    occupancy = build_occupancy(shape, agents)
    terrain = build_default_terrain(shape)
    return SimState(occupancy=occupancy, terrain=terrain, agents=agents)


class SimulatorTests(unittest.TestCase):
    def test_quantize_intent_diagonal(self) -> None:
        self.assertEqual(quantize_intent(-10.0, 10.0), (-1, 1))

    def test_quantize_intent_sector_edges(self) -> None:
        self.assertEqual(quantize_intent(1.0, 0.01), (1, 0))
        self.assertEqual(quantize_intent(1.0, 1.0), (1, 1))
        self.assertEqual(quantize_intent(0.01, 1.0), (0, 1))
        self.assertEqual(quantize_intent(-1.0, 0.01), (-1, 0))

    def test_blocked_by_hard_wall(self) -> None:
        agents = {
            1: AgentState(agent_id=1, row=0, col=0, d_row=-1.0, d_col=0.0, will=1.0),
        }
        state = make_state((4, 4), agents)

        result = step(state)

        self.assertEqual(result.state.agents[1].row, 0)
        self.assertEqual(result.state.agents[1].col, 0)
        self.assertEqual(result.diagnostics.moved_count, 0)
        self.assertEqual(result.diagnostics.blocked_count, 1)

    def test_all_eight_directions_move_correctly(self) -> None:
        directions = [
            (-1, 0),
            (-1, 1),
            (0, 1),
            (1, 1),
            (1, 0),
            (1, -1),
            (0, -1),
            (-1, -1),
        ]

        for index, (d_row, d_col) in enumerate(directions, start=1):
            with self.subTest(direction=(d_row, d_col)):
                agents = {
                    1: AgentState(agent_id=1, row=3, col=3, d_row=float(d_row), d_col=float(d_col), will=1.0),
                }
                state = make_state((7, 7), agents)
                result = step(state)

                self.assertEqual(result.state.agents[1].row, 3 + d_row)
                self.assertEqual(result.state.agents[1].col, 3 + d_col)
                self.assertEqual(result.diagnostics.moved_count, 1)
                self.assertEqual(result.diagnostics.blocked_count, 0)
                self.assertFalse(result.events)

    def test_conflict_resolves_by_will(self) -> None:
        agents = {
            1: AgentState(agent_id=1, row=2, col=1),
            2: AgentState(agent_id=2, row=1, col=2),
        }
        state = make_state((5, 5), agents)

        policy = StaticIntentPolicy(
            {
                1: Intent(d_row=0.0, d_col=1.0, will=0.3),
                2: Intent(d_row=1.0, d_col=0.0, will=0.9),
            }
        )
        result = step(state, policy=policy)

        self.assertEqual(result.state.agents[2].row, 2)
        self.assertEqual(result.state.agents[2].col, 2)
        self.assertEqual(result.state.agents[1].row, 2)
        self.assertEqual(result.state.agents[1].col, 1)
        self.assertEqual(result.diagnostics.conflict_count, 1)
        self.assertEqual(result.diagnostics.tie_break_count, 0)
        self.assertAlmostEqual(result.diagnostics.avg_winner_will, 0.9)

    def test_conflict_tie_breaks_by_lowest_agent_id(self) -> None:
        agents = {
            1: AgentState(agent_id=1, row=2, col=1),
            2: AgentState(agent_id=2, row=1, col=2),
        }
        state = make_state((5, 5), agents)

        policy = StaticIntentPolicy(
            {
                1: Intent(d_row=0.0, d_col=1.0, will=0.8),
                2: Intent(d_row=1.0, d_col=0.0, will=0.8),
            }
        )
        result = step(state, policy=policy)

        self.assertEqual(result.state.agents[1].row, 2)
        self.assertEqual(result.state.agents[1].col, 2)
        self.assertEqual(result.state.agents[2].row, 1)
        self.assertEqual(result.state.agents[2].col, 2)
        self.assertEqual(result.diagnostics.conflict_count, 1)
        self.assertEqual(result.diagnostics.tie_break_count, 1)
        self.assertAlmostEqual(result.diagnostics.avg_winner_will, 0.8)

    def test_replay_is_deterministic(self) -> None:
        agents = {
            1: AgentState(agent_id=1, row=2, col=2, d_row=-1.0, d_col=1.0, will=0.9),
            2: AgentState(agent_id=2, row=3, col=2, d_row=-1.0, d_col=0.0, will=0.7),
            3: AgentState(agent_id=3, row=1, col=3, d_row=1.0, d_col=-1.0, will=0.6),
        }
        state = make_state((6, 6), agents)

        first = step(state)
        second = step(state)

        self.assertEqual(first.state.occupancy, second.state.occupancy)
        self.assertEqual(first.diagnostics, second.diagnostics)

    def test_event_log_reports_conflict_outcomes(self) -> None:
        agents = {
            1: AgentState(agent_id=1, row=2, col=1),
            2: AgentState(agent_id=2, row=1, col=2),
        }
        state = make_state((5, 5), agents)
        policy = StaticIntentPolicy(
            {
                1: Intent(d_row=0.0, d_col=1.0, will=0.9),
                2: Intent(d_row=1.0, d_col=0.0, will=0.1),
            }
        )

        result = step(state, policy=policy, include_events=True)

        events_by_id = {event.agent_id: event for event in result.events}
        self.assertIsNone(events_by_id[1].blocked_reason)
        self.assertTrue(events_by_id[1].won_conflict)
        self.assertEqual(events_by_id[2].blocked_reason, "conflict_lost")
        self.assertFalse(events_by_id[2].won_conflict)

    def test_boundary_edges_and_corners_block_movement(self) -> None:
        cases = [
            ((0, 0), (-1.0, 0.0), (0, 0), "boundary"),
            ((0, 0), (0.0, -1.0), (0, 0), "boundary"),
            ((0, 4), (-1.0, 1.0), (0, 4), "boundary"),
            ((4, 0), (1.0, -1.0), (4, 0), "boundary"),
            ((4, 4), (1.0, 1.0), (4, 4), "boundary"),
            ((0, 2), (-1.0, 0.0), (0, 2), "boundary"),
            ((2, 0), (0.0, -1.0), (2, 0), "boundary"),
            ((2, 4), (0.0, 1.0), (2, 4), "boundary"),
            ((4, 2), (1.0, 0.0), (4, 2), "boundary"),
        ]

        for start, intent_vector, expected_pos, expected_reason in cases:
            with self.subTest(start=start, intent_vector=intent_vector):
                agents = {
                    1: AgentState(
                        agent_id=1,
                        row=start[0],
                        col=start[1],
                        d_row=intent_vector[0],
                        d_col=intent_vector[1],
                        will=1.0,
                    )
                }
                state = make_state((5, 5), agents)
                result = step(state, include_events=True)

                self.assertEqual((result.state.agents[1].row, result.state.agents[1].col), expected_pos)
                self.assertEqual(result.diagnostics.blocked_count, 1)
                self.assertEqual(result.diagnostics.moved_count, 0)
                self.assertEqual(result.events[0].blocked_reason, expected_reason)
                self.assertFalse(result.events[0].won_conflict)

    def test_wall_tile_blocks_movement(self) -> None:
        agents = {
            1: AgentState(agent_id=1, row=1, col=1, d_row=0.0, d_col=1.0, will=1.0),
        }
        occupancy = build_occupancy((3, 3), agents)
        terrain = build_default_terrain((3, 3))
        terrain[1][2] = TILE_WALL
        state = SimState(occupancy=occupancy, terrain=terrain, agents=agents)

        result = step(state, include_events=True)

        self.assertEqual((result.state.agents[1].row, result.state.agents[1].col), (1, 1))
        self.assertEqual(result.events[0].blocked_reason, "terrain")
        self.assertEqual(result.diagnostics.blocked_count, 1)
        self.assertEqual(result.diagnostics.moved_count, 0)


if __name__ == "__main__":
    unittest.main()
