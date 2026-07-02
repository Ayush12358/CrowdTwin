from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BlockedReason = Literal["stay", "boundary", "terrain", "occupied", "conflict_lost"]


@dataclass(frozen=True)
class RunMetadata:
    config_version: str
    policy_version: str
    seed: int | None
    map_version: str | None = None
    run_id: str | None = None


@dataclass(frozen=True)
class AgentStepEvent:
    agent_id: int
    start_pos: tuple[int, int]
    intent_vector: tuple[float, float]
    quantized_move: tuple[int, int]
    resolved_target: tuple[int, int]
    blocked_reason: BlockedReason | None
    won_conflict: bool
    will: float
