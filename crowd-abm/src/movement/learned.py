from __future__ import annotations

from typing import Dict

from src.core.state import SimState
from src.movement.policy import Intent, Policy


class LearnedPolicyStub(Policy):
    """Placeholder for a future trainable policy."""

    def compute_intents(self, state: SimState) -> Dict[int, Intent]:
        raise NotImplementedError("Learned policy is not implemented yet")
