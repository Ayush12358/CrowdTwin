from __future__ import annotations

from typing import Any

import numpy as np

from src.core.errors import PayloadFormatError
from src.core.terrain import TILE_WALL, VALID_TERRAIN_TILES, build_default_terrain


_DIRECTION_VECTORS = np.array(
    [
        [-1, 0],
        [-1, 1],
        [0, 1],
        [1, 1],
        [1, 0],
        [1, -1],
        [0, -1],
        [-1, -1],
    ],
    dtype=np.int8,
)
_DIRECTION_VECTORS_NORM = _DIRECTION_VECTORS.astype(np.float64)
_DIRECTION_VECTORS_NORM /= np.linalg.norm(_DIRECTION_VECTORS_NORM, axis=1, keepdims=True)


def _normalize_occupancy(occupancy_raw: Any) -> np.ndarray:
    occupancy = np.asarray(occupancy_raw, dtype=np.int64)
    if occupancy.ndim != 2:
        raise PayloadFormatError("payload.occupancy must be a 2D matrix")
    if occupancy.shape[0] == 0 or occupancy.shape[1] == 0:
        raise PayloadFormatError("payload.occupancy must be non-empty")
    return occupancy


def _normalize_terrain(terrain_raw: Any, shape: tuple[int, int]) -> np.ndarray:
    if terrain_raw is None:
        terrain_raw = build_default_terrain(shape)
    terrain = np.asarray(terrain_raw, dtype=np.int64)
    if terrain.ndim != 2:
        raise PayloadFormatError("payload.terrain must be a 2D matrix")
    if terrain.shape != shape:
        raise PayloadFormatError("payload.terrain must match occupancy shape")
    if not np.isin(terrain, np.array(list(VALID_TERRAIN_TILES), dtype=np.int64)).all():
        raise PayloadFormatError("payload.terrain contains unsupported tile value")
    return terrain


def _build_agent_arrays(agents_raw: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if not isinstance(agents_raw, list):
        raise PayloadFormatError("payload.agents must be a list")

    count = len(agents_raw)
    agent_id = np.empty(count, dtype=np.int64)
    row = np.empty(count, dtype=np.int64)
    col = np.empty(count, dtype=np.int64)
    d_row = np.empty(count, dtype=np.float64)
    d_col = np.empty(count, dtype=np.float64)
    will = np.empty(count, dtype=np.float64)

    seen_ids = set()
    for idx, raw in enumerate(agents_raw):
        if not isinstance(raw, dict):
            raise PayloadFormatError(f"payload.agents[{idx}] must be an object")
        required = {"agent_id", "row", "col"}
        missing = required.difference(raw.keys())
        if missing:
            raise PayloadFormatError(
                f"payload.agents[{idx}] missing required fields: {sorted(missing)}"
            )
        try:
            aid = int(raw["agent_id"])
            r = int(raw["row"])
            c = int(raw["col"])
            dr = float(raw.get("d_row", 0.0))
            dc = float(raw.get("d_col", 0.0))
            w = float(raw.get("will", 0.0))
        except (TypeError, ValueError) as exc:
            raise PayloadFormatError(f"payload.agents[{idx}] has invalid field type") from exc

        if aid in seen_ids:
            raise PayloadFormatError(f"payload.agents[{idx}] has duplicate agent_id {aid}")
        seen_ids.add(aid)

        agent_id[idx] = aid
        row[idx] = r
        col[idx] = c
        d_row[idx] = dr
        d_col[idx] = dc
        will[idx] = w

    return agent_id, row, col, d_row, d_col, will


def _quantize_bulk(d_row: np.ndarray, d_col: np.ndarray, eps: float = 1e-9) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mag = np.hypot(d_row, d_col)
    moving = mag > eps

    norm_row = np.zeros_like(d_row, dtype=np.float64)
    norm_col = np.zeros_like(d_col, dtype=np.float64)
    norm_row[moving] = d_row[moving] / mag[moving]
    norm_col[moving] = d_col[moving] / mag[moving]

    vectors = np.stack((norm_row, norm_col), axis=1)
    scores = vectors @ _DIRECTION_VECTORS_NORM.T
    best_idx = np.argmax(scores, axis=1)

    move_row = _DIRECTION_VECTORS[best_idx, 0].astype(np.int64)
    move_col = _DIRECTION_VECTORS[best_idx, 1].astype(np.int64)

    move_row[~moving] = 0
    move_col[~moving] = 0

    return move_row, move_col, moving


def _step_arrays(
    occupancy: np.ndarray,
    terrain: np.ndarray,
    agent_id: np.ndarray,
    row: np.ndarray,
    col: np.ndarray,
    d_row: np.ndarray,
    d_col: np.ndarray,
    will: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, float | int]]:
    rows, cols = occupancy.shape

    move_row, move_col, moving = _quantize_bulk(d_row, d_col)

    target_row = row + move_row
    target_col = col + move_col

    in_bounds = (target_row >= 0) & (target_row < rows) & (target_col >= 0) & (target_col < cols)
    candidate_mask = moving & in_bounds

    terrain_ok = np.zeros_like(candidate_mask)
    candidate_idx = np.flatnonzero(candidate_mask)
    if candidate_idx.size > 0:
        terrain_ok[candidate_idx] = terrain[target_row[candidate_idx], target_col[candidate_idx]] != TILE_WALL
    candidate_mask &= terrain_ok

    occupied_ok = np.zeros_like(candidate_mask)
    candidate_idx = np.flatnonzero(candidate_mask)
    if candidate_idx.size > 0:
        occupied_ok[candidate_idx] = occupancy[target_row[candidate_idx], target_col[candidate_idx]] == -1
    candidate_mask &= occupied_ok

    winners = np.zeros(agent_id.shape[0], dtype=bool)
    conflict_count = 0
    tie_break_count = 0
    avg_winner_will = 0.0

    if candidate_idx.size > 0:
        candidate_idx = np.flatnonzero(candidate_mask)
    if candidate_idx.size > 0:
        lin_target = target_row[candidate_idx] * cols + target_col[candidate_idx]

        order = np.lexsort((agent_id[candidate_idx], -will[candidate_idx], lin_target))
        sorted_lin = lin_target[order]
        sorted_will = will[candidate_idx][order]

        is_group_start = np.empty(sorted_lin.shape[0], dtype=bool)
        is_group_start[0] = True
        is_group_start[1:] = sorted_lin[1:] != sorted_lin[:-1]

        starts = np.flatnonzero(is_group_start)
        ends = np.concatenate((starts[1:], np.array([sorted_lin.shape[0]], dtype=np.int64)))
        sizes = ends - starts

        winner_order_idx = starts
        winner_global_idx = candidate_idx[order[winner_order_idx]]
        winners[winner_global_idx] = True

        conflict_groups = sizes > 1
        conflict_count = int(np.sum(conflict_groups))
        if np.any(conflict_groups):
            winner_will = sorted_will[starts[conflict_groups]]
            second_will = sorted_will[starts[conflict_groups] + 1]
            tie_break_count = int(np.sum(second_will == winner_will))

        avg_winner_will = float(np.mean(will[winners])) if np.any(winners) else 0.0

    next_row = row.copy()
    next_col = col.copy()
    next_row[winners] = target_row[winners]
    next_col[winners] = target_col[winners]

    next_occupancy = np.full_like(occupancy, -1)
    next_occupancy[next_row, next_col] = agent_id

    moved_count = int(np.sum(winners))
    blocked_count = int(agent_id.shape[0] - moved_count)

    if moved_count > 0:
        displacement = np.hypot(next_row[winners] - row[winners], next_col[winners] - col[winners])
        avg_displacement = float(np.mean(displacement))
    else:
        avg_displacement = 0.0

    diagnostics: dict[str, float | int] = {
        "moved_count": moved_count,
        "blocked_count": blocked_count,
        "conflict_count": conflict_count,
        "avg_displacement": avg_displacement,
        "tie_break_count": tie_break_count,
        "avg_winner_will": avg_winner_will,
    }

    return next_occupancy, next_row, next_col, diagnostics


def _serialize_agents(
    agent_id: np.ndarray,
    row: np.ndarray,
    col: np.ndarray,
    will: np.ndarray,
    *,
    columnar_output: bool,
) -> Any:
    if columnar_output:
        return {
            "agent_id": agent_id.tolist(),
            "row": row.tolist(),
            "col": col.tolist(),
            "d_row": np.zeros_like(row, dtype=np.float64).tolist(),
            "d_col": np.zeros_like(col, dtype=np.float64).tolist(),
            "will": will.tolist(),
        }

    return [
        {
            "agent_id": int(aid),
            "row": int(r),
            "col": int(c),
            "d_row": 0.0,
            "d_col": 0.0,
            "will": float(w),
        }
        for aid, r, c, w in zip(agent_id, row, col, will)
    ]


def step_payload_bulk(payload: dict[str, Any]) -> dict[str, Any]:
    """Vectorized one-step API for large agent counts.

    Uses NumPy arrays internally and emits columnar agent arrays in payload form.
    """

    if not isinstance(payload, dict):
        raise PayloadFormatError("payload must be a dictionary")

    occupancy = _normalize_occupancy(payload.get("occupancy"))
    terrain = _normalize_terrain(payload.get("terrain"), occupancy.shape)
    columnar_output = bool(payload.get("columnar_output", False))
    agent_id, row, col, d_row, d_col, will = _build_agent_arrays(payload.get("agents"))

    rows, cols = occupancy.shape
    if np.any((row < 0) | (row >= rows) | (col < 0) | (col >= cols)):
        raise PayloadFormatError("payload.agents contains out-of-bounds position")

    next_occupancy, next_row, next_col, diagnostics = _step_arrays(
        occupancy,
        terrain,
        agent_id,
        row,
        col,
        d_row,
        d_col,
        will,
    )

    agents_out = _serialize_agents(
        agent_id,
        next_row,
        next_col,
        will,
        columnar_output=columnar_output,
    )

    return {
        "occupancy": next_occupancy.tolist(),
        "terrain": terrain.tolist(),
        "agents": agents_out,
        "diagnostics": diagnostics,
    }


def simulate_payload_bulk(payload: dict[str, Any], *, steps: int) -> dict[str, Any]:
    """Run multiple bulk steps while keeping arrays resident in memory.

    This is intended for high-throughput fast-forward simulation where repeatedly
    calling the one-step API would add avoidable Python serialization overhead.
    """

    if steps <= 0:
        raise PayloadFormatError("steps must be a positive integer")
    if not isinstance(payload, dict):
        raise PayloadFormatError("payload must be a dictionary")

    occupancy = _normalize_occupancy(payload.get("occupancy"))
    terrain = _normalize_terrain(payload.get("terrain"), occupancy.shape)
    columnar_output = bool(payload.get("columnar_output", False))
    agent_id, row, col, d_row, d_col, will = _build_agent_arrays(payload.get("agents"))

    rows, cols = occupancy.shape
    if np.any((row < 0) | (row >= rows) | (col < 0) | (col >= cols)):
        raise PayloadFormatError("payload.agents contains out-of-bounds position")

    diagnostics: dict[str, float | int] = {
        "moved_count": 0,
        "blocked_count": int(agent_id.shape[0]),
        "conflict_count": 0,
        "avg_displacement": 0.0,
        "tie_break_count": 0,
        "avg_winner_will": 0.0,
    }

    curr_occ = occupancy
    curr_row = row
    curr_col = col

    executed_steps = 0
    for _ in range(steps):
        curr_occ, curr_row, curr_col, diagnostics = _step_arrays(
            curr_occ,
            terrain,
            agent_id,
            curr_row,
            curr_col,
            d_row,
            d_col,
            will,
        )
        executed_steps += 1
        if int(diagnostics["moved_count"]) == 0:
            break

    agents_out = _serialize_agents(
        agent_id,
        curr_row,
        curr_col,
        will,
        columnar_output=columnar_output,
    )

    output: dict[str, Any] = {
        "occupancy": curr_occ.tolist(),
        "terrain": terrain.tolist(),
        "agents": agents_out,
        "diagnostics": diagnostics,
    }

    raw_meta = payload.get("metadata")
    if isinstance(raw_meta, dict):
        output["metadata"] = {
            **raw_meta,
            "simulated_steps": executed_steps,
            "requested_steps": steps,
            "early_converged": executed_steps < steps,
        }

    return output
