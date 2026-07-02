from __future__ import annotations

from src.api import step
from src.core.state import AgentState, SimState
from src.core.terrain import build_default_terrain
from src.core.validators import build_occupancy


def _demo_state() -> SimState:
    agents = {
        1: AgentState(agent_id=1, row=2, col=2, d_row=-1.0, d_col=1.0, will=0.9),
        2: AgentState(agent_id=2, row=3, col=2, d_row=-1.0, d_col=0.0, will=0.7),
    }
    occupancy = build_occupancy((6, 6), agents)
    terrain = build_default_terrain((6, 6))
    return SimState(occupancy=occupancy, terrain=terrain, agents=agents)


def main() -> None:
    state = _demo_state()
    result = step(state)

    print("Moved:", result.diagnostics.moved_count)
    print("Blocked:", result.diagnostics.blocked_count)
    print("Conflicts:", result.diagnostics.conflict_count)
    print("Occupancy:\n", result.state.occupancy)


if __name__ == "__main__":
    main()
