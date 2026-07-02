from __future__ import annotations

import math
from dataclasses import replace
from typing import Dict

from src.backend.base import SimulationBackend
from src.collision.resolver import CandidateMove, resolve_conflicts
from src.core.state import AgentState, SimState, StepDiagnostics, StepResult
from src.core.validators import build_occupancy, validate_state
from src.core.terrain import is_walkable_tile
from src.diagnostics import AgentStepEvent, BlockedReason, RunMetadata
from src.movement.policy import Intent, Policy
from src.core.simulator import quantize_intent


class PythonBackend(SimulationBackend):
    def run_step(
        self,
        state: SimState,
        policy: Policy,
        *,
        include_events: bool = False,
        metadata: RunMetadata | None = None,
    ) -> StepResult:
        validate_state(state)
        intents = policy.compute_intents(state)

        rows = len(state.occupancy)
        cols = len(state.occupancy[0])
        candidates = []
        blocked_ids = set()
        target_counts: Dict[tuple[int, int], int] = {}
        intents_by_agent: Dict[int, Intent] = {}
        quantized_by_agent: Dict[int, tuple[int, int]] = {}
        intended_target_by_agent: Dict[int, tuple[int, int]] = {}
        blocked_reason_by_agent: Dict[int, BlockedReason] = {}

        for agent_id, agent in state.agents.items():
            intent = intents.get(agent_id, Intent(0.0, 0.0, 0.0))
            intents_by_agent[agent_id] = intent
            move_row, move_col = quantize_intent(intent.d_row, intent.d_col)
            quantized_by_agent[agent_id] = (move_row, move_col)

            target_row = agent.row + move_row
            target_col = agent.col + move_col
            intended_target_by_agent[agent_id] = (target_row, target_col)

            if move_row == 0 and move_col == 0:
                blocked_ids.add(agent_id)
                blocked_reason_by_agent[agent_id] = "stay"
                continue

            if target_row < 0 or target_row >= rows or target_col < 0 or target_col >= cols:
                blocked_ids.add(agent_id)
                blocked_reason_by_agent[agent_id] = "boundary"
                continue

            if not is_walkable_tile(state.terrain[target_row][target_col]):
                blocked_ids.add(agent_id)
                blocked_reason_by_agent[agent_id] = "terrain"
                continue

            if state.occupancy[target_row][target_col] != -1:
                blocked_ids.add(agent_id)
                blocked_reason_by_agent[agent_id] = "occupied"
                continue

            target_counts[(target_row, target_col)] = target_counts.get((target_row, target_col), 0) + 1
            candidates.append(
                CandidateMove(
                    agent_id=agent_id,
                    target_row=target_row,
                    target_col=target_col,
                    will=float(intent.will),
                )
            )

        contested_targets = {target for target, count in target_counts.items() if count > 1}
        winners, conflict_stats = resolve_conflicts(candidates)

        new_agents: Dict[int, AgentState] = {}
        for agent_id, agent in state.agents.items():
            winning_move = winners.get(agent_id)
            if winning_move is None:
                if agent_id in intended_target_by_agent and intended_target_by_agent[agent_id] in contested_targets:
                    blocked_reason_by_agent[agent_id] = "conflict_lost"
                blocked_ids.add(agent_id)
                new_agents[agent_id] = replace(agent, d_row=0.0, d_col=0.0)
                continue

            new_agents[agent_id] = replace(
                agent,
                row=winning_move.target_row,
                col=winning_move.target_col,
                d_row=0.0,
                d_col=0.0,
            )

        new_occupancy = build_occupancy((rows, cols), new_agents)

        moved_count = len(winners)
        avg_displacement = 0.0
        if moved_count > 0:
            total_displacement = 0.0
            for move in winners.values():
                total_displacement += math.hypot(
                    move.target_row - state.agents[move.agent_id].row,
                    move.target_col - state.agents[move.agent_id].col,
                )
            avg_displacement = total_displacement / moved_count

        diagnostics = StepDiagnostics(
            moved_count=moved_count,
            blocked_count=len(blocked_ids),
            conflict_count=conflict_stats.conflict_count,
            avg_displacement=avg_displacement,
            tie_break_count=conflict_stats.tie_break_count,
            avg_winner_will=conflict_stats.avg_winner_will,
        )

        events: tuple[AgentStepEvent, ...] = tuple()
        if include_events:
            built_events = []
            for agent_id, agent in state.agents.items():
                intent = intents_by_agent.get(agent_id, Intent(0.0, 0.0, 0.0))
                quantized = quantized_by_agent.get(agent_id, (0, 0))
                final_agent = new_agents[agent_id]
                target = (final_agent.row, final_agent.col)
                winner = agent_id in winners
                blocked_reason = blocked_reason_by_agent.get(agent_id)

                built_events.append(
                    AgentStepEvent(
                        agent_id=agent_id,
                        start_pos=(agent.row, agent.col),
                        intent_vector=(intent.d_row, intent.d_col),
                        quantized_move=quantized,
                        resolved_target=target,
                        blocked_reason=blocked_reason,
                        won_conflict=winner and intended_target_by_agent.get(agent_id) in contested_targets,
                        will=float(intent.will),
                    )
                )
            events = tuple(built_events)

        return StepResult(
            state=SimState(occupancy=new_occupancy, terrain=state.terrain, agents=new_agents),
            diagnostics=diagnostics,
            events=events,
            metadata=metadata,
        )
