from __future__ import annotations

from dataclasses import dataclass, field
from typing import Deque, Tuple
from collections import deque


@dataclass
class TrackState:
    """Holds trajectory state for a single tracked person."""

    track_id: int
    max_history: int = 120
    trajectory: Deque[Tuple[float, float, float]] = field(default_factory=deque)

    def add_point(self, x: float, y: float, t: float) -> None:
        self.trajectory.append((x, y, t))
        while len(self.trajectory) > self.max_history:
            self.trajectory.popleft()


@dataclass
class VectorOutput:
    """Serializable movement vector output."""

    id: int
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    speed: float

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "position": [self.position[0], self.position[1]],
            "velocity": [self.velocity[0], self.velocity[1]],
            "speed": self.speed,
        }
