from __future__ import annotations

from abc import ABC, abstractmethod

from src.core.state import SimState, StepResult
from src.diagnostics import RunMetadata
from src.movement.policy import Policy


class SimulationBackend(ABC):
    @abstractmethod
    def run_step(
        self,
        state: SimState,
        policy: Policy,
        *,
        include_events: bool = False,
        metadata: RunMetadata | None = None,
    ) -> StepResult:
        raise NotImplementedError
