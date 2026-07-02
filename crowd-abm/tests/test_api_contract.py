from __future__ import annotations

import unittest

from src.api import (
    result_to_payload,
    state_from_payload,
    step_payload,
    step_payload_from_tracks,
    terrain_from_elements_file,
    tracks_payload_to_sim_payload,
)
from src.core.errors import PayloadFormatError
from src.core.state import AgentState, SimState, StepDiagnostics, StepResult
from src.core.terrain import TILE_WALL, build_default_terrain
from src.core.validators import build_occupancy


class ApiContractTests(unittest.TestCase):
    def test_state_from_payload_builds_state(self) -> None:
        payload = {
            "occupancy": [[-1, -1], [-1, 1]],
            "terrain": [[-1, -1], [-1, -1]],
            "agents": [
                {"agent_id": 1, "row": 1, "col": 1, "d_row": -1.0, "d_col": 0.0, "will": 0.5}
            ],
        }

        state = state_from_payload(payload)
        self.assertEqual(state.agents[1].row, 1)
        self.assertEqual(state.agents[1].d_row, -1.0)

    def test_state_from_payload_rejects_missing_fields(self) -> None:
        payload = {
            "occupancy": [[-1]],
            "terrain": [[-1]],
            "agents": [{"agent_id": 1, "row": 0}],
        }

        with self.assertRaises(PayloadFormatError):
            state_from_payload(payload)

    def test_state_from_payload_rejects_duplicate_agent_ids(self) -> None:
        payload = {
            "occupancy": [[1, -1]],
            "terrain": [[-1, -1]],
            "agents": [
                {"agent_id": 1, "row": 0, "col": 0},
                {"agent_id": 1, "row": 0, "col": 1},
            ],
        }

        with self.assertRaises(PayloadFormatError):
            state_from_payload(payload)

    def test_state_from_payload_rejects_invalid_occupancy_shape(self) -> None:
        payload = {
            "occupancy": [[-1, -1], [-1]],
            "terrain": [[-1, -1], [-1]],
            "agents": [{"agent_id": 1, "row": 0, "col": 0}],
        }

        with self.assertRaises(PayloadFormatError):
            state_from_payload(payload)

    def test_result_to_payload_serializes_diagnostics(self) -> None:
        agents = {1: AgentState(agent_id=1, row=0, col=0)}
        state = SimState(
            occupancy=build_occupancy((1, 1), agents),
            terrain=build_default_terrain((1, 1)),
            agents=agents,
        )
        result = StepResult(
            state=state,
            diagnostics=StepDiagnostics(
                moved_count=0,
                blocked_count=1,
                conflict_count=0,
                avg_displacement=0.0,
                tie_break_count=0,
                avg_winner_will=0.0,
            ),
        )

        payload = result_to_payload(result)
        self.assertEqual(payload["diagnostics"]["blocked_count"], 1)
        self.assertEqual(payload["diagnostics"]["avg_displacement"], 0.0)

    def test_step_payload_runs_end_to_end(self) -> None:
        payload = {
            "occupancy": [[1, -1], [-1, -1]],
            "terrain": [[-1, -1], [-1, -1]],
            "agents": [
                {"agent_id": 1, "row": 0, "col": 0, "d_row": 1.0, "d_col": 1.0, "will": 1.0}
            ],
        }

        out = step_payload(payload)
        self.assertEqual(out["diagnostics"]["moved_count"], 1)
        self.assertEqual(out["occupancy"][1][1], 1)
        self.assertAlmostEqual(out["diagnostics"]["avg_displacement"], 2**0.5)

    def test_step_payload_includes_events_and_metadata(self) -> None:
        payload = {
            "occupancy": [[1, -1], [-1, -1]],
            "terrain": [[-1, -1], [-1, -1]],
            "agents": [
                {"agent_id": 1, "row": 0, "col": 0, "d_row": 1.0, "d_col": 1.0, "will": 1.0}
            ],
            "metadata": {
                "config_version": "v1",
                "policy_version": "hardcoded-v1",
                "seed": 42,
                "map_version": "map-a",
                "run_id": "run-001",
            },
        }

        out = step_payload(payload, include_events=True, include_metadata=True)

        self.assertIn("events", out)
        self.assertIn("metadata", out)
        self.assertEqual(out["metadata"]["seed"], 42)
        self.assertEqual(len(out["events"]), 1)

        event = out["events"][0]
        expected_keys = {
            "agent_id",
            "start_pos",
            "intent_vector",
            "quantized_move",
            "resolved_target",
            "blocked_reason",
            "won_conflict",
            "will",
        }
        self.assertEqual(set(event.keys()), expected_keys)
        self.assertIn(
            event["blocked_reason"],
            [None, "stay", "boundary", "terrain", "occupied", "conflict_lost"],
        )

    def test_tracks_payload_to_sim_payload_converts_show_shape(self) -> None:
        tracks_payload = {
            "data": {
                "frame_index": 11,
                "result": {
                    "tracks": [
                        {"id": 1, "position": [2.0, 1.0], "velocity": [1.0, 0.0]},
                        {"id": 2, "position": [0.0, 0.0], "velocity": [0.0, 1.0]},
                    ]
                },
            }
        }

        sim_payload = tracks_payload_to_sim_payload(tracks_payload, rows=4, cols=5)

        self.assertEqual(sim_payload["occupancy"][1][2], 1)
        self.assertEqual(sim_payload["occupancy"][0][0], 2)
        self.assertEqual(len(sim_payload["terrain"]), 4)
        self.assertEqual(len(sim_payload["terrain"][0]), 5)
        self.assertEqual(len(sim_payload["agents"]), 2)
        self.assertEqual(sim_payload["metadata"]["run_id"], "11")

    def test_step_payload_from_tracks_runs_end_to_end(self) -> None:
        tracks_payload = {
            "data": {
                "frame_index": 12,
                "result": {
                    "tracks": [
                        {"id": 1, "position": [0.0, 0.0], "velocity": [1.0, 1.0]},
                    ]
                },
            }
        }

        out = step_payload_from_tracks(tracks_payload, rows=3, cols=3, include_metadata=True)

        self.assertEqual(out["diagnostics"]["moved_count"], 1)
        self.assertEqual(out["occupancy"][1][1], 1)
        self.assertEqual(out["metadata"]["run_id"], "12")

    def test_tracks_payload_rejects_overlap(self) -> None:
        tracks_payload = {
            "data": {
                "result": {
                    "tracks": [
                        {"id": 1, "position": [1.0, 1.0], "velocity": [0.0, 0.0]},
                        {"id": 2, "position": [1.0, 1.0], "velocity": [0.0, 0.0]},
                    ]
                }
            }
        }

        with self.assertRaises(PayloadFormatError):
            tracks_payload_to_sim_payload(tracks_payload, rows=3, cols=3)

    def test_state_from_payload_defaults_terrain_when_missing(self) -> None:
        payload = {
            "occupancy": [[1, -1], [-1, -1]],
            "agents": [{"agent_id": 1, "row": 0, "col": 0}],
        }

        state = state_from_payload(payload)
        self.assertEqual(state.terrain, [[-1, -1], [-1, -1]])

    def test_step_payload_blocks_wall_tile_from_terrain(self) -> None:
        payload = {
            "occupancy": [[1, -1], [-1, -1]],
            "terrain": [[-1, TILE_WALL], [-1, -1]],
            "agents": [
                {"agent_id": 1, "row": 0, "col": 0, "d_row": 0.0, "d_col": 1.0, "will": 1.0}
            ],
        }

        out = step_payload(payload, include_events=True)
        self.assertEqual(out["occupancy"][0][0], 1)
        self.assertEqual(out["events"][0]["blocked_reason"], "terrain")

    def test_terrain_from_elements_file_parses_grid(self) -> None:
        terrain = terrain_from_elements_file("elements.md")
        self.assertGreater(len(terrain), 0)
        self.assertGreater(len(terrain[0]), 0)


if __name__ == "__main__":
    unittest.main()
