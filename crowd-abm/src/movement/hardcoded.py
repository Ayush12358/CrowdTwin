from __future__ import annotations

from typing import Dict

from src.core.state import SimState
from src.movement.policy import Intent, Policy


class AgentVectorPolicy(Policy):
    """Policy that reads per-agent vectors already attached to the state."""

    def compute_intents(self, state: SimState) -> Dict[int, Intent]:
        intents: Dict[int, Intent] = {}
        for agent in state.agents.values():
            intents[agent.agent_id] = Intent(
                d_row=agent.d_row,
                d_col=agent.d_col,
                will=agent.will,
            )
        return intents
