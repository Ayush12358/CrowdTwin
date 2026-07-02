from __future__ import annotations

import math
from typing import Any

from src.core.state import SimState, StepResult
from src.diagnostics import RunMetadata
from src.movement.policy import Intent, Policy

# Clockwise direction set in row/col coordinates.
_DIRECTION_VECTORS: tuple[tuple[int, int], ...] = (
    (-1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
    (1, 0),
    (1, -1),
    (0, -1),
    (-1, -1),
)


def quantize_intent(d_row: float, d_col: float, eps: float = 1e-9) -> tuple[int, int]:
    """Map a continuous vector to one of 8 neighbors (or stay if near zero)."""

    magnitude = math.hypot(d_row, d_col)
    if magnitude <= eps:
        return (0, 0)

    best_dir = (0, 0)
    best_score = float("-inf")

    norm_row = d_row / magnitude
    norm_col = d_col / magnitude

    for cand_row, cand_col in _DIRECTION_VECTORS:
        cand_mag = math.hypot(cand_row, cand_col)
        cand_row_n = cand_row / cand_mag
        cand_col_n = cand_col / cand_mag
        score = norm_row * cand_row_n + norm_col * cand_col_n
        if score > best_score:
            best_score = score
            best_dir = (cand_row, cand_col)

    return best_dir


def step(
    state: SimState,
    policy: Policy,
    *,
    include_events: bool = False,
    backend: Any | None = None,
    metadata: RunMetadata | None = None,
) -> StepResult:
    """Run one synchronous movement step using 8-neighbor transitions."""
    if backend is None:
        from src.backend.python_backend import PythonBackend

        backend = PythonBackend()

    return backend.run_step(
        state,
        policy,
        include_events=include_events,
        metadata=metadata,
    )
