from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from src.diagnostics import AgentStepEvent, RunMetadata


@dataclass(frozen=True)
class AgentState:
    """Per-agent state used by the one-step simulator."""

    agent_id: int
    row: int
    col: int
    d_row: float = 0.0
    d_col: float = 0.0
    will: float = 0.0


@dataclass(frozen=True)
class SimState:
    """Simulation state for one step.

    `occupancy` uses -1 for empty cells and stores agent IDs in occupied cells.
    `terrain` stores static map tiles by integer code.
    """

    occupancy: list[list[int]]
    terrain: list[list[int]]
    agents: Dict[int, AgentState]


@dataclass(frozen=True)
class StepDiagnostics:
    moved_count: int
    blocked_count: int
    conflict_count: int
    avg_displacement: float
    tie_break_count: int
    avg_winner_will: float


@dataclass(frozen=True)
class StepResult:
    state: SimState
    diagnostics: StepDiagnostics
    events: tuple[AgentStepEvent, ...] = field(default_factory=tuple)
    metadata: RunMetadata | None = None
