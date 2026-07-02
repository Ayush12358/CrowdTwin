from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

from src.core.state import SimState


@dataclass(frozen=True)
class Intent:
    d_row: float
    d_col: float
    will: float


class Policy(ABC):
    @abstractmethod
    def compute_intents(self, state: SimState) -> Dict[int, Intent]:
        """Return per-agent continuous movement vectors and will score."""
