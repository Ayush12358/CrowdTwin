from __future__ import annotations

from typing import Any

from src.core.errors import PayloadFormatError
from src.core.simulator import step as run_step
from src.core.terrain import VALID_TERRAIN_TILES, build_default_terrain
from src.core.state import AgentState, SimState, StepResult
from src.diagnostics import RunMetadata
from src.backend.base import SimulationBackend
from src.movement.hardcoded import AgentVectorPolicy
from src.movement.policy import Policy
from src.map_loader import load_terrain_from_elements_file
from src.scalable import step_payload_bulk as run_step_payload_bulk
from src.scalable import step_payload_bulk_gpu as run_step_payload_bulk_gpu
from src.scalable.bulk import simulate_payload_bulk as run_simulate_payload_bulk


def step(
    state: SimState,
    policy: Policy | None = None,
    *,
    include_events: bool = False,
    backend: SimulationBackend | None = None,
    metadata: RunMetadata | None = None,
) -> StepResult:
    """Public one-step API used by external orchestrators."""

    effective_policy = policy if policy is not None else AgentVectorPolicy()
    return run_step(
        state=state,
        policy=effective_policy,
        include_events=include_events,
        backend=backend,
        metadata=metadata,
    )


def state_from_payload(payload: dict[str, Any]) -> SimState:
    """Build internal state from a public payload shape."""

    if not isinstance(payload, dict):
        raise PayloadFormatError("payload must be a dictionary")

    occupancy = payload.get("occupancy")
    agents_payload = payload.get("agents")
    terrain = payload.get("terrain")

    if not isinstance(occupancy, list):
        raise PayloadFormatError("payload.occupancy must be a 2D list")
    if not occupancy:
        raise PayloadFormatError("payload.occupancy must not be empty")
    if not all(isinstance(row, list) for row in occupancy):
        raise PayloadFormatError("payload.occupancy must be a 2D list")
    cols = len(occupancy[0])
    if cols == 0:
        raise PayloadFormatError("payload.occupancy must have at least one column")
    if any(len(row) != cols for row in occupancy):
        raise PayloadFormatError("payload.occupancy rows must have consistent length")
    if any(type(cell) is not int for row in occupancy for cell in row):
        raise PayloadFormatError("payload.occupancy cells must be integers")

    if terrain is None:
        terrain = build_default_terrain((len(occupancy), cols))
    if not isinstance(terrain, list):
        raise PayloadFormatError("payload.terrain must be a 2D list")
    if not terrain:
        raise PayloadFormatError("payload.terrain must not be empty")
    if not all(isinstance(row, list) for row in terrain):
        raise PayloadFormatError("payload.terrain must be a 2D list")
    if len(terrain) != len(occupancy) or any(len(row) != cols for row in terrain):
        raise PayloadFormatError("payload.terrain rows must match occupancy shape")
    if any(type(cell) is not int for row in terrain for cell in row):
        raise PayloadFormatError("payload.terrain cells must be integers")
    if any(cell not in VALID_TERRAIN_TILES for row in terrain for cell in row):
        raise PayloadFormatError("payload.terrain contains unsupported tile value")

    if not isinstance(agents_payload, list):
        raise PayloadFormatError("payload.agents must be a list")

    agents: dict[int, AgentState] = {}
    for idx, raw in enumerate(agents_payload):
        if not isinstance(raw, dict):
            raise PayloadFormatError(f"payload.agents[{idx}] must be an object")

        required = {"agent_id", "row", "col"}
        missing = required.difference(raw.keys())
        if missing:
            raise PayloadFormatError(
                f"payload.agents[{idx}] missing required fields: {sorted(missing)}"
            )

        try:
            agent_id = int(raw["agent_id"])
            row = int(raw["row"])
            col = int(raw["col"])
            d_row = float(raw.get("d_row", 0.0))
            d_col = float(raw.get("d_col", 0.0))
            will = float(raw.get("will", 0.0))
        except (TypeError, ValueError) as exc:
            raise PayloadFormatError(
                f"payload.agents[{idx}] has invalid field type"
            ) from exc

        if agent_id in agents:
            raise PayloadFormatError(f"payload.agents[{idx}] has duplicate agent_id {agent_id}")

        agent = AgentState(
            agent_id=agent_id,
            row=row,
            col=col,
            d_row=d_row,
            d_col=d_col,
            will=will,
        )
        agents[agent.agent_id] = agent

    return SimState(occupancy=occupancy, terrain=terrain, agents=agents)


def metadata_from_payload(payload: dict[str, Any]) -> RunMetadata | None:
    raw = payload.get("metadata")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise PayloadFormatError("payload.metadata must be an object")

    required = {"config_version", "policy_version", "seed"}
    missing = required.difference(raw.keys())
    if missing:
        raise PayloadFormatError(f"payload.metadata missing required fields: {sorted(missing)}")

    return RunMetadata(
        config_version=str(raw["config_version"]),
        policy_version=str(raw["policy_version"]),
        seed=None if raw["seed"] is None else int(raw["seed"]),
        map_version=None if raw.get("map_version") is None else str(raw.get("map_version")),
        run_id=None if raw.get("run_id") is None else str(raw.get("run_id")),
    )


def result_to_payload(
    result: StepResult,
    *,
    include_events: bool = False,
    include_metadata: bool = False,
) -> dict[str, Any]:
    """Serialize internal step result to external payload format."""

    agents = []
    for agent in result.state.agents.values():
        agents.append(
            {
                "agent_id": agent.agent_id,
                "row": agent.row,
                "col": agent.col,
                "d_row": agent.d_row,
                "d_col": agent.d_col,
                "will": agent.will,
            }
        )

    output = {
        "occupancy": result.state.occupancy,
        "terrain": result.state.terrain,
        "agents": agents,
        "diagnostics": {
            "moved_count": result.diagnostics.moved_count,
            "blocked_count": result.diagnostics.blocked_count,
            "conflict_count": result.diagnostics.conflict_count,
            "avg_displacement": result.diagnostics.avg_displacement,
            "tie_break_count": result.diagnostics.tie_break_count,
            "avg_winner_will": result.diagnostics.avg_winner_will,
        },
    }

    if include_events:
        output["events"] = [
            {
                "agent_id": event.agent_id,
                "start_pos": [event.start_pos[0], event.start_pos[1]],
                "intent_vector": [event.intent_vector[0], event.intent_vector[1]],
                "quantized_move": [event.quantized_move[0], event.quantized_move[1]],
                "resolved_target": [event.resolved_target[0], event.resolved_target[1]],
                "blocked_reason": event.blocked_reason,
                "won_conflict": event.won_conflict,
                "will": event.will,
            }
            for event in result.events
        ]

    if include_metadata and result.metadata is not None:
        output["metadata"] = {
            "config_version": result.metadata.config_version,
            "policy_version": result.metadata.policy_version,
            "seed": result.metadata.seed,
            "map_version": result.metadata.map_version,
            "run_id": result.metadata.run_id,
        }

    return output


def step_payload(
    payload: dict[str, Any],
    policy: Policy | None = None,
    *,
    include_events: bool = False,
    include_metadata: bool = False,
    backend: SimulationBackend | None = None,
) -> dict[str, Any]:
    """Payload-based one-step API for external orchestrators."""

    state = state_from_payload(payload)
    metadata = metadata_from_payload(payload)
    result = step(
        state=state,
        policy=policy,
        include_events=include_events,
        backend=backend,
        metadata=metadata,
    )
    return result_to_payload(result, include_events=include_events, include_metadata=include_metadata)


def _extract_tracks_payload(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], Any]:
    """Extract tracks and frame index from show.py-style envelope."""

    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        raise PayloadFormatError("payload.data must be an object")

    result = data.get("result")
    if not isinstance(result, dict):
        raise PayloadFormatError("payload.data.result must be an object")

    tracks = result.get("tracks")
    if not isinstance(tracks, list):
        raise PayloadFormatError("payload.data.result.tracks must be a list")

    frame_index = data.get("frame_index")
    filtered = [track for track in tracks if isinstance(track, dict)]
    return filtered, frame_index


def tracks_payload_to_sim_payload(
    payload: dict[str, Any],
    *,
    rows: int,
    cols: int,
    default_will: float = 0.5,
) -> dict[str, Any]:
    """Convert show.py-style JSON into simulator payload format.

    Expected input shape:
    {
        "data": {
            "frame_index": ...,
            "result": {
                "tracks": [{"id": ..., "position": [x, y], "velocity": [vx, vy]}, ...]
            }
        }
    }
    """

    if rows <= 0 or cols <= 0:
        raise PayloadFormatError("rows and cols must be positive")

    tracks, frame_index = _extract_tracks_payload(payload)
    occupancy = [[-1 for _ in range(cols)] for _ in range(rows)]
    terrain = build_default_terrain((rows, cols))
    agents: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    seen_positions: set[tuple[int, int]] = set()

    for idx, track in enumerate(tracks):
        if "id" not in track:
            raise PayloadFormatError(f"payload.data.result.tracks[{idx}] missing id")
        if "position" not in track:
            raise PayloadFormatError(f"payload.data.result.tracks[{idx}] missing position")

        position = track.get("position")
        velocity = track.get("velocity", [0.0, 0.0])
        if not isinstance(position, list) or len(position) != 2:
            raise PayloadFormatError(
                f"payload.data.result.tracks[{idx}].position must be [x, y]"
            )
        if not isinstance(velocity, list) or len(velocity) != 2:
            raise PayloadFormatError(
                f"payload.data.result.tracks[{idx}].velocity must be [vx, vy]"
            )

        try:
            agent_id = int(track["id"])
            col = int(round(float(position[0])))
            row = int(round(float(position[1])))
            d_col = float(velocity[0])
            d_row = float(velocity[1])
        except (TypeError, ValueError) as exc:
            raise PayloadFormatError(
                f"payload.data.result.tracks[{idx}] has invalid field type"
            ) from exc

        if agent_id in seen_ids:
            raise PayloadFormatError(f"payload.data.result.tracks[{idx}] has duplicate id {agent_id}")
        if not (0 <= row < rows and 0 <= col < cols):
            raise PayloadFormatError(
                f"payload.data.result.tracks[{idx}] position out of bounds for {rows}x{cols} grid"
            )
        if (row, col) in seen_positions:
            raise PayloadFormatError(
                f"payload.data.result.tracks[{idx}] overlaps another track position"
            )

        seen_ids.add(agent_id)
        seen_positions.add((row, col))
        occupancy[row][col] = agent_id
        agents.append(
            {
                "agent_id": agent_id,
                "row": row,
                "col": col,
                "d_row": d_row,
                "d_col": d_col,
                "will": default_will,
            }
        )

    return {
        "occupancy": occupancy,
        "terrain": terrain,
        "agents": agents,
        "metadata": {
            "config_version": "ingest-v1",
            "policy_version": "hardcoded-v1",
            "seed": None,
            "map_version": None,
            "run_id": None if frame_index is None else str(frame_index),
        },
    }


def terrain_from_elements_file(path: str) -> list[list[int]]:
    """Load a terrain grid from elements markdown."""

    return load_terrain_from_elements_file(path)


def step_payload_from_tracks(
    payload: dict[str, Any],
    *,
    rows: int,
    cols: int,
    include_events: bool = False,
    include_metadata: bool = False,
    default_will: float = 0.5,
    backend: SimulationBackend | None = None,
) -> dict[str, Any]:
    """Run one simulation step from show.py-style track payload."""

    sim_payload = tracks_payload_to_sim_payload(
        payload,
        rows=rows,
        cols=cols,
        default_will=default_will,
    )
    return step_payload(
        sim_payload,
        include_events=include_events,
        include_metadata=include_metadata,
        backend=backend,
    )


def step_payload_bulk(payload: dict[str, Any]) -> dict[str, Any]:
    """Vectorized one-step payload API for very large agent counts."""

    return run_step_payload_bulk(payload)


def step_payload_bulk_gpu(payload: dict[str, Any], *, fallback_to_cpu: bool = True) -> dict[str, Any]:
    """GPU-accelerated one-step payload API for very large agent counts."""

    return run_step_payload_bulk_gpu(payload, fallback_to_cpu=fallback_to_cpu)


def simulate_payload_bulk(payload: dict[str, Any], *, steps: int) -> dict[str, Any]:
    """Fast-forward multi-step bulk simulation optimized for throughput."""

    return run_simulate_payload_bulk(payload, steps=steps)
