from __future__ import annotations

from typing import Any

from src.core.errors import PayloadFormatError
from src.core.terrain import TILE_WALL, VALID_TERRAIN_TILES, build_default_terrain
from src.scalable.bulk import step_payload_bulk


def step_payload_bulk_gpu(payload: dict[str, Any], *, fallback_to_cpu: bool = True) -> dict[str, Any]:
    """GPU-accelerated bulk payload step using CuPy when available.

    If CuPy is unavailable and `fallback_to_cpu` is True, this falls back to the CPU
    vectorized path.
    """

    try:
        import cupy as cp
    except Exception as exc:  # pragma: no cover - depends on local CUDA/CuPy install
        if fallback_to_cpu:
            return step_payload_bulk(payload)
        raise PayloadFormatError(
            "GPU path requested but CuPy is not available; install cupy-cuda12x or enable CPU fallback"
        ) from exc

    if not isinstance(payload, dict):
        raise PayloadFormatError("payload must be a dictionary")

    occupancy_raw = payload.get("occupancy")
    terrain_raw = payload.get("terrain")
    agents_raw = payload.get("agents")
    if not isinstance(agents_raw, list):
        raise PayloadFormatError("payload.agents must be a list")

    try:
        occupancy = cp.asarray(occupancy_raw, dtype=cp.int64)
    except Exception as exc:
        if fallback_to_cpu:
            return step_payload_bulk(payload)
        raise PayloadFormatError("GPU runtime is unavailable on this machine") from exc

    if occupancy.ndim != 2:
        raise PayloadFormatError("payload.occupancy must be a 2D matrix")
    if occupancy.shape[0] == 0 or occupancy.shape[1] == 0:
        raise PayloadFormatError("payload.occupancy must be non-empty")

    if terrain_raw is None:
        terrain_raw = build_default_terrain((int(occupancy.shape[0]), int(occupancy.shape[1])))
    try:
        terrain = cp.asarray(terrain_raw, dtype=cp.int64)
    except Exception as exc:
        if fallback_to_cpu:
            return step_payload_bulk(payload)
        raise PayloadFormatError("GPU runtime is unavailable on this machine") from exc
    if terrain.ndim != 2:
        raise PayloadFormatError("payload.terrain must be a 2D matrix")
    if terrain.shape != occupancy.shape:
        raise PayloadFormatError("payload.terrain must match occupancy shape")
    allowed_tiles = cp.asarray(sorted(VALID_TERRAIN_TILES), dtype=cp.int64)
    valid_mask = cp.isin(terrain, allowed_tiles)
    if not bool(cp.all(valid_mask).item()):
        raise PayloadFormatError("payload.terrain contains unsupported tile value")

    count = len(agents_raw)
    agent_id = cp.empty(count, dtype=cp.int64)
    row = cp.empty(count, dtype=cp.int64)
    col = cp.empty(count, dtype=cp.int64)
    d_row = cp.empty(count, dtype=cp.float64)
    d_col = cp.empty(count, dtype=cp.float64)
    will = cp.empty(count, dtype=cp.float64)

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

    rows, cols = occupancy.shape
    try:
        out_of_bounds = bool(cp.any((row < 0) | (row >= rows) | (col < 0) | (col >= cols)).item())
    except Exception as exc:
        if fallback_to_cpu:
            return step_payload_bulk(payload)
        raise PayloadFormatError("GPU runtime is unavailable on this machine") from exc

    if out_of_bounds:
        raise PayloadFormatError("payload.agents contains out-of-bounds position")

    directions = cp.array(
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
        dtype=cp.int8,
    )
    directions_norm = directions.astype(cp.float64)
    directions_norm /= cp.linalg.norm(directions_norm, axis=1, keepdims=True)

    try:
        mag = cp.hypot(d_row, d_col)
    except Exception as exc:
        if fallback_to_cpu:
            return step_payload_bulk(payload)
        raise PayloadFormatError("GPU runtime is unavailable on this machine") from exc
    moving = mag > 1e-9
    norm_row = cp.zeros_like(d_row)
    norm_col = cp.zeros_like(d_col)
    norm_row[moving] = d_row[moving] / mag[moving]
    norm_col[moving] = d_col[moving] / mag[moving]

    vectors = cp.stack((norm_row, norm_col), axis=1)
    scores = vectors @ directions_norm.T
    best_idx = cp.argmax(scores, axis=1)
    move_row = directions[best_idx, 0].astype(cp.int64)
    move_col = directions[best_idx, 1].astype(cp.int64)
    move_row[~moving] = 0
    move_col[~moving] = 0

    target_row = row + move_row
    target_col = col + move_col

    in_bounds = (target_row >= 0) & (target_row < rows) & (target_col >= 0) & (target_col < cols)
    candidate_mask = moving & in_bounds
    terrain_ok = cp.zeros_like(candidate_mask)
    candidate_idx = cp.flatnonzero(candidate_mask)
    if candidate_idx.size > 0:
        terrain_ok[candidate_idx] = terrain[target_row[candidate_idx], target_col[candidate_idx]] != TILE_WALL
    candidate_mask &= terrain_ok

    occupied_ok = cp.zeros_like(candidate_mask)
    candidate_idx = cp.flatnonzero(candidate_mask)
    if candidate_idx.size > 0:
        occupied_ok[candidate_idx] = occupancy[target_row[candidate_idx], target_col[candidate_idx]] == -1
    candidate_mask &= occupied_ok

    winners = cp.zeros(agent_id.shape[0], dtype=cp.bool_)
    conflict_count = 0
    tie_break_count = 0

    candidate_idx = cp.flatnonzero(candidate_mask)
    if candidate_idx.size > 0:
        lin_target = target_row[candidate_idx] * cols + target_col[candidate_idx]
        sort_keys = cp.stack(
            (
                agent_id[candidate_idx],
                -will[candidate_idx],
                lin_target,
            ),
            axis=0,
        )
        order = cp.lexsort(sort_keys)
        sorted_lin = lin_target[order]
        sorted_will = will[candidate_idx][order]

        is_group_start = cp.empty(sorted_lin.shape[0], dtype=cp.bool_)
        is_group_start[0] = True
        is_group_start[1:] = sorted_lin[1:] != sorted_lin[:-1]
        starts = cp.flatnonzero(is_group_start)
        ends = cp.concatenate((starts[1:], cp.array([sorted_lin.shape[0]], dtype=cp.int64)))
        sizes = ends - starts

        winner_order_idx = starts
        winner_global_idx = candidate_idx[order[winner_order_idx]]
        winners[winner_global_idx] = True

        conflict_groups = sizes > 1
        conflict_count = int(cp.sum(conflict_groups).item())
        if bool(cp.any(conflict_groups).item()):
            winner_will = sorted_will[starts[conflict_groups]]
            second_will = sorted_will[starts[conflict_groups] + 1]
            tie_break_count = int(cp.sum(second_will == winner_will).item())

    next_row = row.copy()
    next_col = col.copy()
    next_row[winners] = target_row[winners]
    next_col[winners] = target_col[winners]

    next_occupancy = cp.full_like(occupancy, -1)
    next_occupancy[next_row, next_col] = agent_id

    moved_count = int(cp.sum(winners).item())
    blocked_count = int(agent_id.shape[0] - moved_count)
    if moved_count > 0:
        displacement = cp.hypot(next_row[winners] - row[winners], next_col[winners] - col[winners])
        avg_displacement = float(cp.mean(displacement).item())
        avg_winner_will = float(cp.mean(will[winners]).item())
    else:
        avg_displacement = 0.0
        avg_winner_will = 0.0

    columnar_output = bool(payload.get("columnar_output", False))
    agent_id_np = cp.asnumpy(agent_id)
    next_row_np = cp.asnumpy(next_row)
    next_col_np = cp.asnumpy(next_col)
    will_np = cp.asnumpy(will)

    if columnar_output:
        agents_out: Any = {
            "agent_id": agent_id_np.tolist(),
            "row": next_row_np.tolist(),
            "col": next_col_np.tolist(),
            "d_row": [0.0] * count,
            "d_col": [0.0] * count,
            "will": will_np.tolist(),
        }
    else:
        agents_out = [
            {
                "agent_id": int(aid),
                "row": int(r),
                "col": int(c),
                "d_row": 0.0,
                "d_col": 0.0,
                "will": float(w),
            }
            for aid, r, c, w in zip(agent_id_np, next_row_np, next_col_np, will_np)
        ]

    return {
        "occupancy": cp.asnumpy(next_occupancy).tolist(),
        "terrain": cp.asnumpy(terrain).tolist(),
        "agents": agents_out,
        "diagnostics": {
            "moved_count": moved_count,
            "blocked_count": blocked_count,
            "conflict_count": conflict_count,
            "avg_displacement": avg_displacement,
            "tie_break_count": tie_break_count,
            "avg_winner_will": avg_winner_will,
        },
    }
