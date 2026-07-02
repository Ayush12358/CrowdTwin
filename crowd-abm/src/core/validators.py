from __future__ import annotations

from typing import Dict

from .errors import (
    AgentIdMismatchError,
    AgentOutOfBoundsError,
    DuplicateAgentPositionError,
    OccupancyShapeError,
    OccupancyStateMismatchError,
    TerrainShapeError,
    TerrainValueError,
)
from .state import AgentState, SimState
from .terrain import VALID_TERRAIN_TILES


def validate_state(state: SimState) -> None:
    """Validate shape, IDs, and occupancy consistency for a simulation state."""

    if not state.occupancy or not isinstance(state.occupancy, list):
        raise OccupancyShapeError("occupancy must be a non-empty 2D matrix")
    if not isinstance(state.occupancy[0], list):
        raise OccupancyShapeError("occupancy must be a 2D matrix")

    rows = len(state.occupancy)
    cols = len(state.occupancy[0])
    if cols == 0:
        raise OccupancyShapeError("occupancy must have at least one column")
    if any(len(row) != cols for row in state.occupancy):
        raise OccupancyShapeError("occupancy rows must have consistent length")

    if not state.terrain or not isinstance(state.terrain, list):
        raise TerrainShapeError("terrain must be a non-empty 2D matrix")
    if not isinstance(state.terrain[0], list):
        raise TerrainShapeError("terrain must be a 2D matrix")
    if any(len(row) != cols for row in state.terrain):
        raise TerrainShapeError("terrain rows must match occupancy shape")
    if any(type(cell) is not int for row in state.terrain for cell in row):
        raise TerrainValueError("terrain cells must be integers")
    if any(cell not in VALID_TERRAIN_TILES for row in state.terrain for cell in row):
        raise TerrainValueError("terrain contains unsupported tile value")

    seen_positions = set()

    for agent_id, agent in state.agents.items():
        if agent_id != agent.agent_id:
            raise AgentIdMismatchError("agent key must match AgentState.agent_id")
        if not (0 <= agent.row < rows and 0 <= agent.col < cols):
            raise AgentOutOfBoundsError(f"agent {agent_id} position out of bounds")
        if (agent.row, agent.col) in seen_positions:
            raise DuplicateAgentPositionError("multiple agents occupy the same position")
        seen_positions.add((agent.row, agent.col))

    expected = [[-1 for _ in range(cols)] for _ in range(rows)]
    for agent in state.agents.values():
        expected[agent.row][agent.col] = agent.agent_id

    if state.occupancy != expected:
        raise OccupancyStateMismatchError("occupancy grid is inconsistent with agent table")


def build_occupancy(shape: tuple[int, int], agents: Dict[int, AgentState]) -> list[list[int]]:
    rows, cols = shape
    if rows <= 0 or cols <= 0:
        raise OccupancyShapeError("shape must contain positive rows and columns")

    occupancy = [[-1 for _ in range(cols)] for _ in range(rows)]
    for agent in agents.values():
        if not (0 <= agent.row < rows and 0 <= agent.col < cols):
            raise AgentOutOfBoundsError(f"agent {agent.agent_id} position out of bounds")
        if occupancy[agent.row][agent.col] != -1:
            raise DuplicateAgentPositionError("duplicate agent position when building occupancy")
        occupancy[agent.row][agent.col] = agent.agent_id
    return occupancy
