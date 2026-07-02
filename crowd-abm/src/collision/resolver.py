from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class CandidateMove:
    agent_id: int
    target_row: int
    target_col: int
    will: float


@dataclass(frozen=True)
class ConflictStats:
    conflict_count: int
    tie_break_count: int
    avg_winner_will: float


def resolve_conflicts(candidates: Iterable[CandidateMove]) -> tuple[Dict[int, CandidateMove], ConflictStats]:
    """Resolve target-cell conflicts using highest will then lowest agent_id."""

    grouped: Dict[Tuple[int, int], List[CandidateMove]] = defaultdict(list)
    for move in candidates:
        grouped[(move.target_row, move.target_col)].append(move)

    winners: Dict[int, CandidateMove] = {}
    conflict_count = 0
    tie_break_count = 0
    winner_wills: List[float] = []

    for grouped_moves in grouped.values():
        if len(grouped_moves) > 1:
            conflict_count += 1
            max_will = max(m.will for m in grouped_moves)
            contenders = [m for m in grouped_moves if m.will == max_will]
            if len(contenders) > 1:
                tie_break_count += 1
        winner = max(grouped_moves, key=lambda m: (m.will, -m.agent_id))
        winners[winner.agent_id] = winner
        winner_wills.append(winner.will)

    avg_winner_will = 0.0
    if winner_wills:
        avg_winner_will = sum(winner_wills) / len(winner_wills)

    stats = ConflictStats(
        conflict_count=conflict_count,
        tie_break_count=tie_break_count,
        avg_winner_will=avg_winner_will,
    )

    return winners, stats
